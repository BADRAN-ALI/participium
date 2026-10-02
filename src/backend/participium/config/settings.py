from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from participium.config.constants import APP_NAME


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    app_name: str
    secret_key: str
    debug: bool
    frontend_origin: str
    host: str
    port: int
    auto_init_db: bool
    bootstrap_reference_data: bool
    bootstrap_demo_data: bool
    mail_backend: str
    mail_from: str
    mail_outbox_dir: Path
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_use_tls: bool
    expose_verification_links: bool
    media_root: Path
    max_content_length: int
    instance_path: Path

    @classmethod
    def from_env(cls) -> "Settings":
        base_dir = Path(__file__).resolve().parents[2]
        load_dotenv(base_dir / ".env")

        instance_path = base_dir / "instance"
        instance_path.mkdir(parents=True, exist_ok=True)

        media_root = Path(os.getenv("MEDIA_ROOT", str(base_dir / "participium" / "static" / "uploads")))
        media_root.mkdir(parents=True, exist_ok=True)

        outbox_dir = Path(os.getenv("MAIL_OUTBOX_DIR", str(instance_path / "outbox")))
        outbox_dir.mkdir(parents=True, exist_ok=True)

        return cls(
            app_name=APP_NAME,
            secret_key=os.getenv("SECRET_KEY", "change-me"),
            debug=os.getenv("FLASK_ENV", "development").lower() == "development",
            frontend_origin=os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "5050")),
            auto_init_db=_as_bool(os.getenv("AUTO_INIT_DB"), True),
            bootstrap_reference_data=_as_bool(os.getenv("BOOTSTRAP_REFERENCE_DATA"), True),
            bootstrap_demo_data=_as_bool(os.getenv("BOOTSTRAP_DEMO_DATA"), True),
            mail_backend=os.getenv("MAIL_BACKEND", "console"),
            mail_from=os.getenv("MAIL_FROM", "noreply@participium.local"),
            mail_outbox_dir=outbox_dir,
            smtp_host=os.getenv("SMTP_HOST") or None,
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME") or None,
            smtp_password=os.getenv("SMTP_PASSWORD") or None,
            smtp_use_tls=_as_bool(os.getenv("SMTP_USE_TLS"), True),
            expose_verification_links=_as_bool(os.getenv("EXPOSE_VERIFICATION_LINKS"), True),
            media_root=media_root,
            max_content_length=int(os.getenv("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024))),
            instance_path=instance_path,
        )
