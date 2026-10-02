from __future__ import annotations

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from participium.models.base import Base, TimestampMixin
from participium.models.enums import ReportStatus


class Report(TimestampMixin, Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(nullable=False, default=False)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus), nullable=False, default=ReportStatus.PENDING_APPROVAL
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reporter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)

    reporter = relationship("User", back_populates="reports")
    category = relationship("Category")
    photos = relationship("ReportPhoto", back_populates="report", cascade="all, delete-orphan")
    status_history = relationship(
        "ReportStatusHistory", back_populates="report", cascade="all, delete-orphan"
    )
    followers = relationship("ReportFollower", back_populates="report", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="report", cascade="all, delete-orphan")


class ReportPhoto(TimestampMixin, Base):
    __tablename__ = "report_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)

    report = relationship("Report", back_populates="photos")


class ReportStatusHistory(Base):
    __tablename__ = "report_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    previous_status: Mapped[ReportStatus | None] = mapped_column(Enum(ReportStatus), nullable=True)
    new_status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False, server_default=func.now())

    report = relationship("Report", back_populates="status_history")
    changed_by = relationship("User")


class ReportFollower(Base):
    __tablename__ = "report_followers"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False, server_default=func.now())

    report = relationship("Report", back_populates="followers")
    user = relationship("User")
