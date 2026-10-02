from __future__ import annotations

from pathlib import Path

from participium.config.constants import DEFAULT_CATEGORIES
from participium.core.security import hash_password
from participium.models.category import Category
from participium.models.enums import ReportStatus, Role
from participium.models.report import Report, ReportPhoto, ReportStatusHistory
from participium.models.user import User


def seed_reference_data(session):
    existing_names = {category.name for category in session.query(Category).all()}
    for name in DEFAULT_CATEGORIES:
        if name not in existing_names:
            session.add(Category(name=name, is_active=True))
    session.commit()


def _ensure_demo_photo(media_root, filename: str) -> str:
    if media_root is None:
        return filename
    upload_dir = Path(media_root)
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / filename
    if not destination.exists():
        destination.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">'
            '<rect width="640" height="360" fill="#e7f1ef"/>'
            '<circle cx="320" cy="180" r="72" fill="#0f766e"/>'
            '<text x="320" y="300" text-anchor="middle" font-family="Arial" font-size="32" fill="#1f2a2e">'
            'Participium demo photo</text></svg>',
            encoding="utf-8",
        )
    return filename


def seed_demo_data(session, media_root=None):
    categories = {category.name: category for category in session.query(Category).all()}
    users = {
        "citizen@example.com": {
            "username": "citizen",
            "first_name": "Marco",
            "last_name": "Citizen",
            "role": Role.CITIZEN,
            "category_name": None,
            "password": "Citizen123!",
        },
        "operator@example.com": {
            "username": "operator",
            "first_name": "Lucia",
            "last_name": "Operator",
            "role": Role.OPERATOR,
            "category_name": "Roads and Urban Furniture",
            "password": "Operator123!",
        },
        "admin@example.com": {
            "username": "admin",
            "first_name": "Admin",
            "last_name": "User",
            "role": Role.ADMIN,
            "category_name": None,
            "password": "Admin123!",
        },
    }

    for email, payload in users.items():
        if session.query(User).filter_by(email=email).first():
            continue
        category = categories.get(payload["category_name"]) if payload["category_name"] else None
        session.add(
            User(
                username=payload["username"],
                first_name=payload["first_name"],
                last_name=payload["last_name"],
                email=email,
                password_hash=hash_password(payload["password"]),
                role=payload["role"],
                category_id=category.id if category else None,
                is_active=True,
                is_email_verified=True,
                email_notifications_enabled=True,
            )
        )
    session.commit()

    if session.query(Report).count() > 0:
        return

    citizen = session.query(User).filter_by(email="citizen@example.com").first()
    category = session.query(Category).filter_by(name="Roads and Urban Furniture").first()
    if not citizen or not category:
        return

    pending = Report(
        title="Damaged bench near school",
        description="A bench is broken and needs maintenance.",
        latitude=45.0703,
        longitude=7.6869,
        is_anonymous=False,
        status=ReportStatus.PENDING_APPROVAL,
        reporter_id=citizen.id,
        category_id=category.id,
    )
    public_report = Report(
        title="Pothole on Via Roma",
        description="Large pothole creating danger for bikes.",
        latitude=45.0678,
        longitude=7.6825,
        is_anonymous=True,
        status=ReportStatus.RESOLVED,
        reporter_id=citizen.id,
        category_id=category.id,
    )
    session.add_all([pending, public_report])
    session.flush()

    demo_photo = _ensure_demo_photo(media_root, "demo-report-photo.svg")
    session.add_all(
        [
            ReportPhoto(
                report_id=pending.id,
                file_path=demo_photo,
                original_filename="demo-report-photo.svg",
                content_type="image/svg+xml",
            ),
            ReportPhoto(
                report_id=public_report.id,
                file_path=demo_photo,
                original_filename="demo-report-photo.svg",
                content_type="image/svg+xml",
            ),
        ]
    )
    session.add_all(
        [
            ReportStatusHistory(
                report_id=pending.id,
                previous_status=None,
                new_status=ReportStatus.PENDING_APPROVAL,
                note="Demo report pending review.",
                changed_by_id=citizen.id,
            ),
            ReportStatusHistory(
                report_id=public_report.id,
                previous_status=None,
                new_status=ReportStatus.PENDING_APPROVAL,
                note="Demo report submitted.",
                changed_by_id=citizen.id,
            ),
            ReportStatusHistory(
                report_id=public_report.id,
                previous_status=ReportStatus.PENDING_APPROVAL,
                new_status=ReportStatus.ASSIGNED,
                note="Accepted for category 'Roads and Urban Furniture'.",
                changed_by_id=session.query(User).filter_by(email="operator@example.com").first().id,
            ),
            ReportStatusHistory(
                report_id=public_report.id,
                previous_status=ReportStatus.ASSIGNED,
                new_status=ReportStatus.RESOLVED,
                note="Repair completed.",
                changed_by_id=session.query(User).filter_by(email="operator@example.com").first().id,
            ),
        ]
    )
    session.commit()
