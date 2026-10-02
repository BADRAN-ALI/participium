from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flask import current_app

from participium.controllers import (
    AdminController,
    AuthController,
    OperatorController,
    ReportController,
    StatisticsController,
    UserController,
)
from participium.database import get_session
from participium.repositories import (
    CategoryRepository,
    MessageRepository,
    NotificationRepository,
    ReportRepository,
    TokenRepository,
    UserRepository,
)
from participium.services import (
    AuthService,
    CategoryService,
    LocalFileStorageService,
    MessagingService,
    NotificationService,
    ReportService,
    StatisticsService,
    UserService,
    build_email_gateway,
)


@dataclass
class ControllerBundle:
    auth: AuthController
    users: UserController
    reports: ReportController
    operators: OperatorController
    admin: AdminController
    statistics: StatisticsController
    repositories: dict[str, Any]


class AppContainer:
    def __init__(self, settings):
        self.settings = settings
        self.email_gateway = build_email_gateway(settings)
        self.storage_service = LocalFileStorageService(settings.media_root)

    def build_controllers(self) -> ControllerBundle:
        session = get_session()
        user_repository = UserRepository(session)
        category_repository = CategoryRepository(session)
        report_repository = ReportRepository(session)
        message_repository = MessageRepository(session)
        notification_repository = NotificationRepository(session)
        token_repository = TokenRepository(session)

        notification_service = NotificationService(session, notification_repository, self.email_gateway)
        auth_service = AuthService(session, user_repository, token_repository, self.email_gateway)
        user_service = UserService(
            session,
            user_repository,
            category_repository,
            token_repository,
            notification_repository,
            self.storage_service,
        )
        category_service = CategoryService(session, category_repository)
        report_service = ReportService(
            session,
            report_repository,
            category_repository,
            self.storage_service,
            notification_service,
        )
        messaging_service = MessagingService(
            session,
            report_repository,
            message_repository,
            notification_service,
        )
        statistics_service = StatisticsService(report_repository)

        repositories = {
            "users": user_repository,
            "categories": category_repository,
            "reports": report_repository,
            "messages": message_repository,
            "notifications": notification_repository,
            "tokens": token_repository,
        }

        return ControllerBundle(
            auth=AuthController(auth_service),
            users=UserController(user_service, notification_service),
            reports=ReportController(report_service, messaging_service, notification_service),
            operators=OperatorController(report_service, notification_service),
            admin=AdminController(category_service, user_service, statistics_service),
            statistics=StatisticsController(statistics_service),
            repositories=repositories,
        )


def get_controllers() -> ControllerBundle:
    return current_app.extensions["container"].build_controllers()
