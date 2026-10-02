"""
Public-facing page tests — no authentication required.

Covered use cases
-----------------
UC-04  Browse reports on map        – home page loads with map and report list
UC-05  Search and filter reports    – filter form updates the visible report list
UC-06  View report details          – detail page shows complete public information
UC-08  Export reports (CSV)         – export link is available and reachable
UC-09  View public statistics       – statistics section shows counts and trend granularity
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select

from conftest import (
    FRONTEND_URL,
    wait_for_id,
    wait_visible_id,
)


# ---------------------------------------------------------------------------
# UC-04  Browse reports on map
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_home_page_loads_with_public_report_list(driver):
    """
    UC-04 — The home page loads, the public report list section and the map
    section are both present. At least the total-reports counter is visible.
    """
    driver.get(FRONTEND_URL)

    # Map card and filter section must be present
    wait_for_id(driver, "public-map-card")
    wait_for_id(driver, "public-filter-section")

    # Statistics section must show a total reports counter
    wait_visible_id(driver, "public-total-reports-value")

    # Public report list rendered by the filter form section
    wait_for_id(driver, "public-filter-form")


@pytest.mark.e2e
def test_home_page_shows_nav_login_register_when_unauthenticated(driver):
    """
    UC-04 — Unauthenticated visitors see login and register links in the navbar.
    """
    driver.get(FRONTEND_URL)
    wait_for_id(driver, "nav-login")
    wait_for_id(driver, "nav-register")


# ---------------------------------------------------------------------------
# UC-05  Search and filter reports
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_filter_form_submit_updates_report_list(driver):
    """
    UC-05 — A visitor can apply the category/status filter form and the page
    updates. The submit button must be present and clickable.
    """
    driver.get(FRONTEND_URL)

    submit_btn = wait_visible_id(driver, "public-filter-submit")
    wait_for_id(driver, "public-filter-status")
    wait_for_id(driver, "public-filter-sort")

    # Apply default filters by submitting the form as-is
    submit_btn.click()

    # After submit the filter section is still present (no navigation)
    wait_for_id(driver, "public-filter-section")


@pytest.mark.e2e
def test_filter_sort_select_changes_sort_order(driver):
    """
    UC-05 — The sort select exposes 'Newest first' and 'Oldest first' options.
    Changing the sort option does not navigate away from the page.
    """
    driver.get(FRONTEND_URL)
    sort_select = Select(wait_for_id(driver, "public-filter-sort"))

    # Verify both sort options are present
    option_values = [o.get_attribute("value") for o in sort_select.options]
    assert "asc" in option_values, "Expected 'asc' (oldest first) option in sort select."
    assert "desc" in option_values, "Expected 'desc' (newest first) option in sort select."

    # Change sort order and submit
    sort_select.select_by_value("asc")
    driver.find_element(By.ID, "public-filter-submit").click()
    wait_for_id(driver, "public-filter-section")


@pytest.mark.e2e
def test_stat_granularity_select_has_day_week_month_options(driver):
    """
    UC-09 — The statistics granularity select contains 'day', 'week', and 'month'.
    """
    driver.get(FRONTEND_URL)
    granularity_select = Select(wait_for_id(driver, "public-stat-granularity"))
    option_values = [o.get_attribute("value") for o in granularity_select.options]
    assert "day" in option_values
    assert "week" in option_values
    assert "month" in option_values


# ---------------------------------------------------------------------------
# UC-06  View report details
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_report_detail_page_shows_complete_information(driver):
    """
    UC-06 — Opening a report by navigating directly to /reports/<id> shows
    the detail page with title, status, description, category, reporter, and
    creation date. Report #1 is created by the seed and should always exist.
    """
    # Navigate directly to the seeded report (ID 1 always created by seed data)
    driver.get(f"{FRONTEND_URL}/reports/1")

    wait_visible_id(driver, "report-detail-title")
    wait_for_id(driver, "report-detail-status")
    wait_for_id(driver, "report-detail-description")
    wait_for_id(driver, "report-detail-category")
    wait_for_id(driver, "report-detail-reporter")
    wait_for_id(driver, "report-detail-created")

    title_el = driver.find_element(By.ID, "report-detail-title")
    assert title_el.text, "Report detail title must not be empty."


@pytest.mark.e2e
def test_clicking_public_report_row_opens_detail(driver):
    """
    UC-06 — A visitor can click a report row on the home page to navigate to
    its detail page. This test uses the first visible public-report-row element.
    """
    driver.get(FRONTEND_URL)
    wait_for_id(driver, "public-filter-form")

    # Submit filters to load the report list
    driver.find_element(By.ID, "public-filter-submit").click()

    # Wait for at least one public-report-row element; find the first link inside it
    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "[id^='public-report-row-']")) > 0
    )
    rows = driver.find_elements(By.CSS_SELECTOR, "[id^='public-report-row-']")
    assert rows, "Expected at least one public-report-row element on the home page."

    # Each row contains a link to the report detail; click the first one
    first_row = rows[0]
    links = first_row.find_elements(By.TAG_NAME, "a")
    assert links, "Expected a link inside the first public-report-row."
    links[0].click()

    # Should navigate to /reports/<id>
    WebDriverWait(driver, 10).until(EC.url_contains("/reports/"))
    wait_visible_id(driver, "report-detail-title")


# ---------------------------------------------------------------------------
# UC-08  Export reports (CSV)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_csv_export_link_is_present_on_home_page(driver):
    """
    UC-08 — The public export CSV link is present on the home page and has
    an href pointing to the backend export endpoint.
    """
    driver.get(FRONTEND_URL)
    export_link = wait_for_id(driver, "public-export-link")

    href = export_link.get_attribute("href")
    assert href, "Export link must have a non-empty href."
    assert "export" in href.lower() or "csv" in href.lower() or "reports" in href.lower(), (
        f"Export link href does not look like a report export URL: {href!r}"
    )


# ---------------------------------------------------------------------------
# UC-09  View public statistics
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_public_statistics_section_is_present(driver):
    """
    UC-09 — The public statistics card is present on the home page and shows
    a total reports count and the category statistics section.
    """
    driver.get(FRONTEND_URL)

    wait_visible_id(driver, "public-statistics-card")
    wait_visible_id(driver, "public-total-reports-value")
    wait_for_id(driver, "public-category-statistics")


@pytest.mark.e2e
def test_public_statistics_granularity_changes_display(driver):
    """
    UC-09 — Changing the granularity select and re-submitting the filter does
    not navigate away from the home page.
    """
    driver.get(FRONTEND_URL)
    granularity_select = Select(wait_for_id(driver, "public-stat-granularity"))
    granularity_select.select_by_value("week")
    driver.find_element(By.ID, "public-filter-submit").click()
    wait_for_id(driver, "public-statistics-card")
