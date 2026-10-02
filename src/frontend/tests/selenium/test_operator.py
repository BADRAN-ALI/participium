"""
Operator workflow tests.

Covered use cases
-----------------
UC-10  Manage report        – operator assigns a pending report and updates its status
UC-11  Send message         – operator sends a message to the citizen via the report detail

The test creates its own report data through the UI (citizen submits, operator
manages) so the suite remains repeatable regardless of existing seed state.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select

from conftest import (
    FRONTEND_URL,
    CITIZEN_EMAIL,
    CITIZEN_PASSWORD,
    OPERATOR_EMAIL,
    OPERATOR_PASSWORD,
    login,
    logout,
    unique_suffix,
    wait_for_id,
    wait_visible_id,
    wait_clickable_id,
    wait_url_contains,
    wait_url_not,
)


def _create_report_as_citizen(driver, report_title):
    """
    Helper: log in as the seeded citizen, create a report with the given title
    using the 'Roads and Urban Furniture' category (the operator's category),
    and log out. Returns after successful submission.
    """
    login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)
    wait_url_contains(driver, "/dashboard")

    driver.get(f"{FRONTEND_URL}/reports/new")
    wait_for_id(driver, "new-report-form")

    driver.find_element(By.ID, "report-title").send_keys(report_title)
    driver.find_element(By.ID, "report-description").send_keys(
        "Test report created by Selenium for operator workflow testing."
    )

    # Select 'Roads and Urban Furniture' which is the seeded operator's category
    category_select = Select(driver.find_element(By.ID, "report-category"))
    try:
        category_select.select_by_visible_text("Roads and Urban Furniture")
    except Exception:
        # Fall back to first available category if the seeded one is not present
        options = [o for o in category_select.options if o.get_attribute("value")]
        assert options, "No category options found."
        options[0].click()

    driver.find_element(By.ID, "report-latitude").clear()
    driver.find_element(By.ID, "report-latitude").send_keys("45.0703")
    driver.find_element(By.ID, "report-longitude").clear()
    driver.find_element(By.ID, "report-longitude").send_keys("7.6869")

    driver.find_element(By.ID, "new-report-submit").click()

    # Wait for navigation away from the new-report page
    wait_url_not(driver, f"{FRONTEND_URL}/reports/new")

    logout(driver)


def _find_pending_row_id_by_title(driver, report_title):
    """
    Helper: scan all pending-report-row-* elements for one whose title cell
    contains report_title. Returns the numeric report ID or raises.
    """
    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "[id^='pending-report-row-']")) > 0
    )
    rows = driver.find_elements(By.CSS_SELECTOR, "[id^='pending-report-row-']")
    for row in rows:
        if report_title in row.text:
            row_id = row.get_attribute("id")  # e.g. "pending-report-row-42"
            return row_id.split("-")[-1]
    raise AssertionError(
        f"Could not find a pending report row containing title {report_title!r}. "
        f"Rows found: {[r.text for r in rows]}"
    )


# ---------------------------------------------------------------------------
# UC-10  Manage report (assign + status update)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_operator_assigns_pending_report(driver):
    """
    UC-10 — An operator can see a pending report and assign it.

    Flow:
    1. Citizen creates a report in the operator's category.
    2. Operator navigates to /operator, finds the report in the pending table.
    3. Operator clicks the assign button; the report moves to the assigned table.
    """
    suffix = unique_suffix()
    report_title = f"Operator Assign Test {suffix}"

    # Step 1 – create report as citizen
    _create_report_as_citizen(driver, report_title)

    # Step 2 – log in as operator
    login(driver, OPERATOR_EMAIL, OPERATOR_PASSWORD)
    wait_url_contains(driver, "/operator")

    wait_for_id(driver, "pending-reports-table")

    # Step 3 – locate the pending report by title and assign it
    report_id = _find_pending_row_id_by_title(driver, report_title)

    assign_btn_id = f"pending-report-assign-{report_id}"
    assign_btn = wait_clickable_id(driver, assign_btn_id)
    assign_btn.click()

    # After assignment the report should appear in the assigned table
    assigned_row_id = f"assigned-report-row-{report_id}"
    wait_for_id(driver, assigned_row_id)
    assigned_row = driver.find_element(By.ID, assigned_row_id)
    assert report_title in assigned_row.text, (
        f"Expected assigned row {assigned_row_id!r} to contain the report title."
    )


@pytest.mark.e2e
def test_operator_updates_report_status(driver):
    """
    UC-10 — An operator can change a report status to 'In Progress'.

    Flow:
    1. Citizen creates a report; operator assigns it.
    2. Operator uses the status select to set 'in_progress', provides a note,
       and submits the update.
    3. The status displayed in the assigned row changes.
    """
    suffix = unique_suffix()
    report_title = f"Status Update Test {suffix}"

    # Step 1 – create and assign
    _create_report_as_citizen(driver, report_title)

    login(driver, OPERATOR_EMAIL, OPERATOR_PASSWORD)
    wait_url_contains(driver, "/operator")
    wait_for_id(driver, "pending-reports-table")

    report_id = _find_pending_row_id_by_title(driver, report_title)

    # Assign the report
    assign_btn = wait_clickable_id(driver, f"pending-report-assign-{report_id}")
    assign_btn.click()

    # Wait for it to appear in assigned table
    wait_for_id(driver, f"assigned-report-row-{report_id}")

    # Step 2 – update status to in_progress
    status_select_id = f"assigned-report-status-{report_id}"
    status_select = Select(wait_for_id(driver, status_select_id))
    status_select.select_by_value("in_progress")

    note_input_id = f"assigned-report-note-{report_id}"
    note_input = wait_for_id(driver, note_input_id)
    note_input.clear()
    note_input.send_keys("Work started — Selenium automated test note.")

    update_btn_id = f"assigned-report-update-{report_id}"
    update_btn = wait_clickable_id(driver, update_btn_id)
    update_btn.click()

    # Step 3 – verify the status changed in the row
    assigned_row = WebDriverWait(driver, 10).until(
        lambda d: d.find_element(By.ID, f"assigned-report-row-{report_id}")
    )
    assert "in_progress" in assigned_row.text.lower() or "in progress" in assigned_row.text.lower(), (
        f"Expected 'in_progress' status in assigned row after update, got: {assigned_row.text!r}"
    )


# ---------------------------------------------------------------------------
# UC-11  Send message to citizen
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_operator_can_send_message_to_citizen(driver):
    """
    UC-11 — After assigning a report, an operator can open the report detail
    page and send a message to the citizen via the messaging form.
    """
    suffix = unique_suffix()
    report_title = f"Message Test {suffix}"
    message_body = f"Operator test message {suffix}"

    # Create report as citizen, then assign it as operator
    _create_report_as_citizen(driver, report_title)

    login(driver, OPERATOR_EMAIL, OPERATOR_PASSWORD)
    wait_url_contains(driver, "/operator")
    wait_for_id(driver, "pending-reports-table")

    report_id = _find_pending_row_id_by_title(driver, report_title)

    # Assign the report
    assign_btn = wait_clickable_id(driver, f"pending-report-assign-{report_id}")
    assign_btn.click()
    wait_for_id(driver, f"assigned-report-row-{report_id}")

    # Open the report detail from the assigned row link
    open_link_id = f"assigned-report-row-{report_id}-open-detail"
    open_link = wait_clickable_id(driver, open_link_id)
    open_link.click()

    wait_url_contains(driver, f"/reports/{report_id}")
    wait_visible_id(driver, "report-detail-title")

    # Send a message via the messaging form
    message_input = wait_clickable_id(driver, "report-message-body")
    message_input.clear()
    message_input.send_keys(message_body)

    send_btn = wait_clickable_id(driver, "report-message-submit")
    send_btn.click()

    # Wait for the message to appear in the messages list
    WebDriverWait(driver, 10).until(
        lambda d: any(
            message_body in el.text
            for el in d.find_elements(By.CSS_SELECTOR, "[id^='message-item-']")
        )
    )
    messages = driver.find_elements(By.CSS_SELECTOR, "[id^='message-item-']")
    message_texts = [m.text for m in messages]
    assert any(message_body in t for t in message_texts), (
        f"Expected message {message_body!r} to appear in the messages list."
    )
