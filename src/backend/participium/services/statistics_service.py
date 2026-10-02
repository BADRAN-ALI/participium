from __future__ import annotations

from collections import Counter, defaultdict
from math import ceil


class StatisticsService:
    def __init__(self, report_repository):
        self.report_repository = report_repository

    def public_statistics(self, granularity: str = "day"):
        reports = self.report_repository.list_reports(public_only=True)
        return {
            "reports_by_category": dict(Counter(report.category.name for report in reports)),
            "trends": self._aggregate_trends(reports, granularity),
            "total_reports": len(reports),
        }

    def admin_statistics(self):
        reports = self.report_repository.list_all()
        by_status = Counter(report.status.value for report in reports)
        by_type = Counter(report.category.name for report in reports)
        by_type_and_status = Counter(f"{report.category.name} | {report.status.value}" for report in reports)
        by_reporter = Counter(self._reporter_label(report) for report in reports)
        by_reporter_and_type = Counter(
            f"{self._reporter_label(report)} | {report.category.name}" for report in reports
        )
        by_reporter_type_status = Counter(
            f"{self._reporter_label(report)} | {report.category.name} | {report.status.value}" for report in reports
        )
        top_1 = self._top_percent_breakdown(reports, 1)
        top_5 = self._top_percent_breakdown(reports, 5)
        return {
            "reports_by_status": dict(by_status),
            "reports_by_type": dict(by_type),
            "reports_by_type_and_status": dict(by_type_and_status),
            "reports_by_reporter": dict(by_reporter),
            "reports_by_reporter_and_type": dict(by_reporter_and_type),
            "reports_by_reporter_type_and_status": dict(by_reporter_type_status),
            "top_1_percent_by_type": top_1,
            "top_5_percent_by_type": top_5,
        }

    def _aggregate_trends(self, reports, granularity: str):
        buckets = defaultdict(int)
        for report in reports:
            created_at = report.created_at
            if granularity == "month":
                key = created_at.strftime("%Y-%m")
            elif granularity == "week":
                iso_year, iso_week, _ = created_at.isocalendar()
                key = f"{iso_year}-W{iso_week:02d}"
            else:
                key = created_at.strftime("%Y-%m-%d")
            buckets[key] += 1
        return dict(sorted(buckets.items()))

    def _top_percent_breakdown(self, reports, percent: int):
        counts_by_reporter = Counter(self._reporter_label(report) for report in reports)
        reporter_count = max(1, ceil(len(counts_by_reporter) * (percent / 100))) if counts_by_reporter else 0
        top_reporters = {label for label, _ in counts_by_reporter.most_common(reporter_count)}
        breakdown = Counter(report.category.name for report in reports if self._reporter_label(report) in top_reporters)
        return dict(breakdown)

    @staticmethod
    def _reporter_label(report):
        if not report.reporter:
            return "Deleted Citizen"
        return f"{report.reporter.username} ({report.reporter.id})"
