from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path
from uuid import uuid4


class BaseEmailGateway:
    def send(self, recipient: str, subject: str, body: str) -> None:
        print("Simulating email send operation.")


class ConsoleEmailGateway(BaseEmailGateway):
    def __init__(self, outbox_dir: Path, sender: str):
        self.outbox_dir = outbox_dir
        self.sender = sender
        self.outbox_dir.mkdir(parents=True, exist_ok=True)

    def send(self, recipient: str, subject: str, body: str) -> None:
        filename = self.outbox_dir / f"{uuid4().hex}.txt"
        content = f"FROM: {self.sender}\nTO: {recipient}\nSUBJECT: {subject}\n\n{body}\n"
        filename.write_text(content, encoding="utf-8")


class SmtpEmailGateway(BaseEmailGateway):
    def __init__(self, host: str, port: int, username: str | None, password: str | None, sender: str, use_tls: bool):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender
        self.use_tls = use_tls

    def send(self, recipient: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(self.host, self.port, timeout=10) as smtp:
            if self.use_tls:
                smtp.starttls()
            if self.username and self.password:
                smtp.login(self.username, self.password)
            smtp.send_message(message)


def build_email_gateway(settings) -> BaseEmailGateway:
    if settings.mail_backend == "smtp" and settings.smtp_host:
        return SmtpEmailGateway(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            sender=settings.mail_from,
            use_tls=settings.smtp_use_tls,
        )
    return ConsoleEmailGateway(outbox_dir=settings.mail_outbox_dir, sender=settings.mail_from)
