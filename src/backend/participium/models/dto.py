from __future__ import annotations

from typing import NotRequired, TypedDict


class CategoryDTO(TypedDict):
    id: int
    name: str
    is_active: bool
    created_at: str | None


class PartyDTO(TypedDict):
    id: int | None
    display_name: str
    role: str | None


class ReporterDTO(TypedDict):
    id: int | None
    display_name: str
    role: NotRequired[str | None]


class UserDTO(TypedDict):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    role: str
    category_id: int | None
    category: CategoryDTO | None
    is_active: bool
    is_email_verified: bool
    email_notifications_enabled: bool
    profile_picture_path: str | None
    profile_picture_url: str | None
    created_at: str | None


class NotificationDTO(TypedDict):
    id: int
    type: str
    title: str
    body: str
    report_id: int | None
    is_read: bool
    created_at: str | None


class MessageDTO(TypedDict):
    id: int
    report_id: int
    body: str
    sender: PartyDTO
    recipient: PartyDTO
    created_at: str | None


class PhotoDTO(TypedDict):
    id: int
    file_path: str
    url: str | None
    original_filename: str
    content_type: str


class ReportSummaryDTO(TypedDict):
    id: int
    title: str
    description: str
    category: CategoryDTO
    status: str
    rejection_reason: str | None
    is_anonymous: bool
    reporter: ReporterDTO | PartyDTO
    latitude: float
    longitude: float
    photos: list[PhotoDTO]
    followers_count: int
    is_followed_by_current_user: bool
    is_public: bool
    created_at: str | None
    updated_at: str | None


class StatusHistoryDTO(TypedDict):
    id: int
    previous_status: str | None
    new_status: str
    note: str | None
    changed_by: PartyDTO
    created_at: str | None


class ReportDetailDTO(ReportSummaryDTO):
    can_access_messages: bool
    status_history: list[StatusHistoryDTO]
    messages: NotRequired[list[MessageDTO]]
