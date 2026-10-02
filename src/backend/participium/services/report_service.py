from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from werkzeug.datastructures import FileStorage

from participium.config.constants import OPERATOR_ROLES, PUBLIC_VISIBLE_STATUSES
from participium.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from participium.core.status_flow import ensure_transition_allowed
from participium.models.enums import ReportStatus, Role
from participium.models.report import Report, ReportFollower, ReportPhoto, ReportStatusHistory
from participium.models.user import User

if TYPE_CHECKING:
    from participium.services.notification_service import NotificationService


class ReportService:
    def __init__(
        self,
        session,
        report_repository,
        category_repository,
        storage_service,
        notification_service: NotificationService | None = None,
    ):
        self.session = session
        self.report_repository = report_repository
        self.category_repository = category_repository
        self.storage_service = storage_service
        self.notification_service = notification_service

    def list_public_reports(
        self,
        category_id: int | None = None,
        status: ReportStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sort: str = "desc",
    ) -> list[Report]:
        """List reports that are publicly visible, optionally filtered.

        Inputs:
            category_id: optional category filter.
            status: optional exact status filter.
            date_from: optional lower bound on creation timestamp.
            date_to: optional upper bound on creation timestamp.
            sort: creation timestamp order; meaningful values are `asc` and `desc`.

        Returns:
            A list of public `Report` objects matching the filters.

        Raises:
            No documented domain exception.
        """
        return self.report_repository.list_reports(
            public_only=True,
            category_id=category_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            sort=sort,
        )

    def list_user_reports(self, user: User) -> list[Report]:
        return self.report_repository.list_user_reports(user.id)

    def get_report(self, report_id: int) -> Report:
        report = self.report_repository.get_by_id(report_id)
        if not report:
            raise NotFoundError("Report not found.")
        return report

    def get_accessible_report(self, report_id: int, user: User | None = None) -> Report:
        report = self.get_report(report_id)
        if self.is_public(report):
            return report
        if user is None:
            raise AuthorizationError("You do not have access to this report.")
        if report.reporter_id == user.id or user.role == Role.ADMIN:
            return report
        if user.role == Role.OPERATOR and user.category_id == report.category_id:
            return report
        raise AuthorizationError("You do not have access to this report.")

    def create_report(
        self,
        reporter: User,
        category_id: int | str | None,
        title: str | None,
        description: str | None,
        latitude: float | str | None,
        longitude: float | str | None,
        photos: list[FileStorage],
        is_anonymous: bool = False,
    ) -> Report:
        """Create a new citizen report.

        Inputs:
            reporter: authenticated citizen creating the report.
            category_id: identifier of the chosen category.
            title: short report title.
            description: detailed report description.
            latitude: report latitude.
            longitude: report longitude.
            photos: uploaded photos; only entries with a filename count as valid.
            is_anonymous: whether the report hides the reporter publicly.

        Returns:
            The created `Report`, reloaded after persistence.

        Raises:
            ValidationError: if `category_id` is missing, malformed, unknown, or refers to an inactive category.
            ValidationError: if `title` or `description` is missing.
            ValidationError: if `latitude` or `longitude` is missing.
            ValidationError: if coordinates cannot be converted to valid numeric values.
            ValidationError: if there are no valid uploaded photos.
            ValidationError: if more than 3 valid photos are provided.
        """
        try:
            resolved_category_id = int(category_id) if category_id is not None else None
        except (TypeError, ValueError) as exc:
            raise ValidationError("A valid active category is required.") from exc

        category = self.category_repository.get_by_id(resolved_category_id) if resolved_category_id else None
        if not category or not category.is_active:
            raise ValidationError("A valid active category is required.")
        if not title or not description:
            raise ValidationError("Title and description are required.")
        if latitude is None or longitude is None:
            raise ValidationError("Latitude and longitude are required.")

        try:
            resolved_latitude = float(latitude)
            resolved_longitude = float(longitude)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Latitude and longitude must be valid numbers.") from exc

        valid_photos = [photo for photo in photos if photo and photo.filename]
        if not valid_photos:
            raise ValidationError("At least one photo is required.")
        if len(valid_photos) > 3:
            raise ValidationError("A report can contain at most 3 photos.")

        report = Report(
            title=title.strip(),
            description=description.strip(),
            latitude=resolved_latitude,
            longitude=resolved_longitude,
            is_anonymous=bool(is_anonymous),
            status=ReportStatus.PENDING_APPROVAL,
            reporter_id=reporter.id,
            category_id=category.id,
        )
        self.report_repository.add(report)
        self.session.flush()

        for photo in valid_photos:
            stored_path = self.storage_service.save(photo)
            self.report_repository.add_photo(
                ReportPhoto(
                    report_id=report.id,
                    file_path=stored_path,
                    original_filename=photo.filename,
                    content_type=photo.content_type,
                )
            )

        self.report_repository.add_status_entry(
            ReportStatusHistory(
                report_id=report.id,
                previous_status=None,
                new_status=ReportStatus.PENDING_APPROVAL,
                note="Report submitted by citizen.",
                changed_by_id=reporter.id,
            )
        )
        self.session.commit()
        return self.get_report(report.id)

    def follow_report(self, report_id: int, user: User) -> Report:
        report = self.get_report(report_id)
        if not self.is_public(report):
            raise ValidationError("Only published reports can be followed.")
        if self.report_repository.get_follower(report.id, user.id):
            return report
        self.report_repository.add_follower(ReportFollower(report_id=report.id, user_id=user.id))
        self.session.commit()
        return self.get_report(report.id)

    def unfollow_report(self, report_id: int, user: User) -> Report:
        report = self.get_report(report_id)
        follower = self.report_repository.get_follower(report.id, user.id)
        if follower:
            self.report_repository.remove_follower(follower)
            self.session.commit()
        return self.get_report(report.id)

    def list_pending_reports(self, filters: dict) -> list[Report]:
        return self.report_repository.list_pending(
            category_id=filters.get("category_id"),
            date_from=filters.get("date_from"),
            date_to=filters.get("date_to"),
        )

    def list_operator_reports(self, user: User) -> list[Report]:
        return self.report_repository.list_operator_reports(user.role, user.category_id)

    def assign_report(self, report_id: int, operator: User) -> Report:
        if operator.role not in {Role.ADMIN, Role.OPERATOR}:
            raise AuthorizationError("Only operators or admins can assign reports.")
        report = self.get_report(report_id)
        self._ensure_operator_category_access(operator, report)
        if report.status != ReportStatus.PENDING_APPROVAL:
            raise ValidationError("Only pending reports can be assigned.")
        previous_status = report.status
        report.status = ReportStatus.ASSIGNED
        self.report_repository.add_status_entry(
            ReportStatusHistory(
                report_id=report.id,
                previous_status=previous_status,
                new_status=ReportStatus.ASSIGNED,
                note=f"Accepted for category '{report.category.name}'.",
                changed_by_id=operator.id,
            )
        )
        self.notification_service.notify_status_change(
            recipients=self._recipients(report),
            report=report,
            body=f"Report #{report.id} has been assigned for handling in category '{report.category.name}'.",
        )
        self.session.commit()
        return self.get_report(report.id)

    def update_status(
        self,
        report_id: int,
        operator: User,
        next_status_value: str,
        note: str | None = None,
    ) -> Report:
        """Update the workflow status of an existing report.

        Inputs:
            report_id: identifier of the target report.
            operator: admin or operator attempting the transition.
            next_status_value: raw target status value.
            note: optional note; mandatory for rejections.

        Returns:
            The updated `Report`, reloaded after persistence.

        Raises:
            AuthorizationError: if `operator` is not allowed to update report statuses.
            AuthorizationError: if an operator tries to update a report outside their category.
            NotFoundError: if the report does not exist.
            ValidationError: if `next_status_value` is not a valid report status.
            ValidationError: if a rejection is requested without a note.
            ValidationError: if the transition is not allowed by the workflow rules.
        """
        if operator.role not in OPERATOR_ROLES:
            raise AuthorizationError("Only operators and admins can update report status.")
        report = self.get_report(report_id)
        self._ensure_operator_category_access(operator, report)
        try:
            next_status = ReportStatus(next_status_value)
        except ValueError as exc:
            raise ValidationError("Invalid report status.") from exc
        if next_status == ReportStatus.REJECTED and not note:
            raise ValidationError("Rejection reason is required.")
        ensure_transition_allowed(report.status, next_status)
        previous_status = report.status
        report.status = next_status
        report.rejection_reason = note if next_status == ReportStatus.REJECTED else None
        self.report_repository.add_status_entry(
            ReportStatusHistory(
                report_id=report.id,
                previous_status=previous_status,
                new_status=next_status,
                note=note,
                changed_by_id=operator.id,
            )
        )
        self.notification_service.notify_status_change(
            recipients=self._recipients(report),
            report=report,
            body=f"Report #{report.id} is now '{next_status.value}'.",
        )
        self.session.commit()
        return self.get_report(report.id)

    def export_rows(
        self,
        category_id: int | None = None,
        status: ReportStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sort: str = "desc",
    ) -> list[dict[str, int | float | str]]:
        reports = self.list_public_reports(
            category_id=category_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            sort=sort,
        )
        rows = []
        for report in reports:
            rows.append(
                {
                    "id": report.id,
                    "title": report.title,
                    "category": report.category.name,
                    "status": report.status.value,
                    "created_at": report.created_at.isoformat(),
                    "latitude": report.latitude,
                    "longitude": report.longitude,
                }
            )
        return rows

    @staticmethod
    def is_public(report: Report) -> bool:
        return report.status in PUBLIC_VISIBLE_STATUSES

    @staticmethod
    def _recipients(report: Report) -> list[User]:
        recipients = [report.reporter]
        recipients.extend([follower.user for follower in report.followers])
        return [recipient for recipient in recipients if recipient is not None]

    @staticmethod
    def _ensure_operator_category_access(operator: User, report: Report) -> None:
        if operator.role == Role.ADMIN:
            return
        if operator.role != Role.OPERATOR:
            raise AuthorizationError("Only operators and admins can manage reports.")
        if operator.category_id != report.category_id:
            raise AuthorizationError("This report does not belong to your category.")
