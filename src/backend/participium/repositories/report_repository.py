from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from participium.config.constants import PUBLIC_VISIBLE_STATUSES
from participium.models.enums import ReportStatus, Role
from participium.models.message import Message
from participium.models.report import Report, ReportFollower, ReportPhoto, ReportStatusHistory
from participium.repositories.base import BaseRepository


class ReportRepository(BaseRepository):
    def _detail_options(self):
        return (
            joinedload(Report.category),
            joinedload(Report.reporter),
            selectinload(Report.photos),
            selectinload(Report.status_history).joinedload(ReportStatusHistory.changed_by),
            selectinload(Report.followers).joinedload(ReportFollower.user),
            selectinload(Report.messages).joinedload(Message.sender),
            selectinload(Report.messages).joinedload(Message.recipient),
        )

    def add(self, report: Report) -> None:
        self.session.add(report)
        return report

    def add_photo(self, photo: ReportPhoto) -> None:
        self.session.add(photo)
        return photo

    def add_status_entry(self, status_entry: ReportStatusHistory) -> None:
        self.session.add(status_entry)
        return status_entry

    def add_follower(self, follower: ReportFollower) -> ReportFollower:
        self.session.add(follower)
        return follower

    def get_follower(self, report_id: int, user_id: int) -> ReportFollower | None:
        query = select(ReportFollower).where(
            ReportFollower.report_id == report_id,
            ReportFollower.user_id == user_id,
        )
        return self.session.scalar(query)

    def remove_follower(self, follower: ReportFollower) -> None:
        self.session.delete(follower)

    def get_by_id(self, report_id: int) -> Report | None:
        query = select(Report).where(Report.id == report_id).options(*self._detail_options())
        return self.session.scalar(query)

    def list_reports(
        self,
        *,
        public_only: bool = False,
        category_id: int | None = None,
        status: ReportStatus | None = None,
        date_from=None,
        date_to=None,
        sort: str = "desc",
    ) -> list[Report]:
        query = select(Report).options(*self._detail_options())
        if public_only:
            query = query.where(Report.status.in_(list(PUBLIC_VISIBLE_STATUSES)))
        if category_id:
            query = query.where(Report.category_id == category_id)
        if status:
            query = query.where(Report.status == status)
        if date_from:
            query = query.where(Report.created_at >= date_from)
        if date_to:
            query = query.where(Report.created_at <= date_to)
        order_by = Report.created_at.asc() if sort == "asc" else Report.created_at.desc()
        query = query.order_by(order_by)
        return list(self.session.scalars(query).unique())

    def list_user_reports(self, user_id: int) -> list[Report]:
        query = (
            select(Report)
            .where(Report.reporter_id == user_id)
            .options(*self._detail_options())
            .order_by(Report.created_at.desc())
        )
        return list(self.session.scalars(query).unique())

    def list_pending(self, category_id: int | None = None, date_from=None, date_to=None) -> list[Report]:
        query = (
            select(Report)
            .where(Report.status == ReportStatus.PENDING_APPROVAL)
            .options(*self._detail_options())
            .order_by(Report.created_at.asc())
        )
        if category_id:
            query = query.where(Report.category_id == category_id)
        if date_from:
            query = query.where(Report.created_at >= date_from)
        if date_to:
            query = query.where(Report.created_at <= date_to)
        return list(self.session.scalars(query).unique())

    def list_for_category(self, category_id: int | None) -> list[Report]:
        query = (
            select(Report)
            .where(Report.status != ReportStatus.PENDING_APPROVAL)
            .options(*self._detail_options())
            .order_by(Report.updated_at.desc())
        )
        if category_id is not None:
            query = query.where(Report.category_id == category_id)
        return list(self.session.scalars(query).unique())

    def list_operator_reports(self, role: Role, category_id: int | None = None) -> list[Report]:
        if role == Role.OPERATOR:
            return self.list_for_category(category_id)
        return self.list_for_category(None)

    def list_followers(self, report_id: int) -> list[ReportFollower]:
        query = select(ReportFollower).where(ReportFollower.report_id == report_id)
        return list(self.session.scalars(query))

    def list_all(self) -> list[Report]:
        return self.list_reports(public_only=False)
