from __future__ import annotations

from participium.services.statistics_service import StatisticsService


class StatisticsController:
    def __init__(self, statistics_service: StatisticsService):
        self.statistics_service = statistics_service

    def public_statistics(self, granularity: str = "day") -> dict[str, dict[str, int] | int]:
        return self.statistics_service.public_statistics(granularity)
