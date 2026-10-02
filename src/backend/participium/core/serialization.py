from __future__ import annotations

from typing import cast

from participium.config.constants import PUBLIC_VISIBLE_STATUSES
from participium.models.category import Category
from participium.models.enums import Role
from participium.models.message import Message
from participium.models.notification import Notification
from participium.models.report import Report, ReportPhoto
from participium.models.user import User
from participium.models.dto import (
    CategoryDTO,
    MessageDTO,
    NotificationDTO,
    PartyDTO,
    PhotoDTO,
    ReportDetailDTO,
    ReportSummaryDTO,
    ReporterDTO,
    UserDTO,
)


def serialize_user(user: User) -> UserDTO:
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role.value,
        "category_id": user.category_id,
        "category": serialize_category(user.category) if user.category else None,
        "is_active": user.is_active,
        "is_email_verified": user.is_email_verified,
        "email_notifications_enabled": user.email_notifications_enabled,
        "profile_picture_path": user.profile_picture_path,
        "profile_picture_url": _media_url(user.profile_picture_path),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def serialize_category(category: Category) -> CategoryDTO:
    return {
        "id": category.id,
        "name": category.name,
        "is_active": category.is_active,
        "created_at": category.created_at.isoformat() if category.created_at else None,
    }


def serialize_notification(notification: Notification) -> NotificationDTO:
    return {
        "id": notification.id,
        "type": notification.type.value,
        "title": notification.title,
        "body": notification.body,
        "report_id": notification.report_id,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
    }


def serialize_message(message: Message) -> MessageDTO:
    return {
        "id": message.id,
        "report_id": message.report_id,
        "body": message.body,
        "sender": _serialize_party(message.sender),
        "recipient": _serialize_party(message.recipient),
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


def serialize_report_summary(report: Report, viewer: User | None = None) -> ReportSummaryDTO:
    return {
        "id": report.id,
        "title": report.title,
        "description": report.description,
        "category": serialize_category(report.category),
        "status": report.status.value,
        "rejection_reason": report.rejection_reason,
        "is_anonymous": report.is_anonymous,
        "reporter": _serialize_reporter(report, viewer),
        "latitude": report.latitude,
        "longitude": report.longitude,
        "photos": [serialize_photo(photo) for photo in report.photos],
        "followers_count": len(report.followers),
        "is_followed_by_current_user": _viewer_follows_report(report, viewer),
        "is_public": report.status in PUBLIC_VISIBLE_STATUSES,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
    }


def serialize_report_detail(
    report: Report,
    viewer: User | None = None,
    include_messages: bool = False,
) -> ReportDetailDTO:
    data = serialize_report_summary(report, viewer=viewer)
    data["can_access_messages"] = include_messages
    data["status_history"] = [
        {
            "id": item.id,
            "previous_status": item.previous_status.value if item.previous_status else None,
            "new_status": item.new_status.value,
            "note": item.note,
            "changed_by": _serialize_party(item.changed_by),
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in sorted(report.status_history, key=lambda entry: entry.created_at)
    ]
    if include_messages:
        data["messages"] = [
            serialize_message(message)
            for message in sorted(report.messages, key=lambda msg: msg.created_at)
        ]
    return cast(ReportDetailDTO, data)


def serialize_photo(photo: ReportPhoto) -> PhotoDTO:
    return {
        "id": photo.id,
        "file_path": photo.file_path,
        "url": _media_url(photo.file_path),
        "original_filename": photo.original_filename,
        "content_type": photo.content_type,
    }


def _media_url(file_path: str | None) -> str | None:
    if not file_path:
        return None
    return f"/static/uploads/{file_path}"


def _serialize_party(user: User | None) -> PartyDTO:
    if user is None:
        return {"id": None, "display_name": "Deleted User", "role": None}
    return {
        "id": user.id,
        "display_name": f"{user.first_name} {user.last_name}".strip() or user.username,
        "role": user.role.value,
    }


def _serialize_reporter(report: Report, viewer: User | None = None) -> ReporterDTO | PartyDTO:
    if report.reporter is None:
        return {"display_name": "Deleted Citizen", "id": None}
    if not report.is_anonymous:
        return _serialize_party(report.reporter)
    if viewer is None:
        return {"display_name": "Anonymous Citizen", "id": None}
    if viewer.role == Role.ADMIN:
        return _serialize_party(report.reporter)
    if viewer.role == Role.OPERATOR and viewer.category_id == report.category_id:
        return _serialize_party(report.reporter)
    if report.reporter_id == viewer.id:
        return _serialize_party(report.reporter)
    return {"display_name": "Anonymous Citizen", "id": None}


def _viewer_follows_report(report: Report, viewer: User | None = None) -> bool:
    if viewer is None:
        return False
    return any(follower.user_id == viewer.id for follower in report.followers)
