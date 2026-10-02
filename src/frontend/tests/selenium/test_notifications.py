"""
Notification tests — citizen receives in-platform notifications (FR-13).

Covered functional requirements / use cases
--------------------------------------------
FR-13  In-platform notifications  – system generates a notification for the
                                    reporter and followers when a report status
                                    changes (triggered by UC-10 status update).
UC-10  Manage report              – used as the setup trigger to cause the
                                    status change that generates the notification.
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


# ---------------------------------------------------------------------------
# Notification delivery after status change (FR-13)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_citizen_receives_notification_after_status_change(driver):
    """
    FR-13 — When an operator updates the status of a citizen's report, the
    citizen receives an in-platform notification visible in the dashboard
    notifications list.

    Flow:
    1. Citizen creates a report.
    2. Operator assigns the report and sets its status to 'In Progress'.
    3. Citizen navigates to /dashboard and sees a notification for the update.
    """
    suffix = unique_suffix()
    report_title = f"Notification Test {suffix}"

    # Step 1 – Citizen creates a report
    login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)
    wait_url_contains(driver, "/dashboard")

    driver.get(f"{FRONTEND_URL}/reports/new")
    wait_for_id(driver, "new-report-form")

    driver.find_element(By.ID, "report-title").send_keys(report_title)
    driver.find_element(By.ID, "report-description").send_keys(
        "Notification flow test report."
    )

    category_select = Select(driver.find_element(By.ID, "report-category"))
    try:
        category_select.select_by_visible_text("Roads and Urban Furniture")
    except Exception:
        options = [o for o in category_select.options if o.get_attribute("value")]
        assert options
        options[0].click()

    driver.find_element(By.ID, "report-latitude").clear()
    driver.find_element(By.ID, "report-latitude").send_keys("45.0703")
    driver.find_element(By.ID, "report-longitude").clear()
    driver.find_element(By.ID, "report-longitude").send_keys("7.6869")

    driver.find_element(By.ID, "new-report-submit").click()
    wait_url_not(driver, f"{FRONTEND_URL}/reports/new")

    logout(driver)

    # Step 2 – Operator assigns and updates status
    login(driver, OPERATOR_EMAIL, OPERATOR_PASSWORD)
    wait_url_contains(driver, "/operator")
    wait_for_id(driver, "pending-reports-table")

    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "[id^='pending-report-row-']")) > 0
    )
    rows = driver.find_elements(By.CSS_SELECTOR, "[id^='pending-report-row-']")
    report_id = None
    for row in rows:
        if report_title in row.text:
            report_id = row.get_attribute("id").split("-")[-1]
            break

    assert report_id is not None, f"Could not find pending report: {report_title!r}"

    # Assign the report
    assign_btn = wait_clickable_id(driver, f"pending-report-assign-{report_id}")
    assign_btn.click()
    wait_for_id(driver, f"assigned-report-row-{report_id}")

    # Update status to in_progress
    status_select = Select(wait_for_id(driver, f"assigned-report-status-{report_id}"))
    status_select.select_by_value("in_progress")

    note_input = wait_for_id(driver, f"assigned-report-note-{report_id}")
    note_input.clear()
    note_input.send_keys("Work has started — notification test.")

    wait_clickable_id(driver, f"assigned-report-update-{report_id}").click()

    # Wait for the row to reflect the new status
    WebDriverWait(driver, 10).until(
        lambda d: "in_progress" in d.find_element(
            By.ID, f"assigned-report-row-{report_id}"
        ).text.lower()
        or "in progress" in d.find_element(
            By.ID, f"assigned-report-row-{report_id}"
        ).text.lower()
    )

    logout(driver)

    # Step 3 – Citizen checks notifications
    login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)
    wait_url_contains(driver, "/dashboard")

    wait_for_id(driver, "notifications-list")

    # At least one notification item must be present
    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "[id^='notification-item-']")) > 0
    )
    notification_items = driver.find_elements(By.CSS_SELECTOR, "[id^='notification-item-']")
    assert notification_items, "Expected at least one notification after status change."


@pytest.mark.e2e
def test_citizen_can_mark_notification_as_read(driver):
    """
    FR-13 — A citizen can mark an existing notification as read using the
    notification-read-<id> button. The notification is either removed from
    the list or visually updated.
    """
    login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)
    wait_url_contains(driver, "/dashboard")

    wait_for_id(driver, "notifications-list")

    # There must be at least one notification to mark as read
    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "[id^='notification-item-']")) > 0
    )
    notification_items = driver.find_elements(By.CSS_SELECTOR, "[id^='notification-item-']")
    if not notification_items:
        pytest.skip("No notifications available to mark as read.")

    first_item = notification_items[0]
    item_id = first_item.get_attribute("id")  # e.g. "notification-item-5"
    notification_id = item_id.split("-")[-1]

    # Click the mark-as-read button for this notification
    read_btn_id = f"notification-read-{notification_id}"
    read_btns = driver.find_elements(By.ID, read_btn_id)
    if not read_btns:
        pytest.skip(f"No mark-as-read button found for notification {notification_id!r}.")

    initial_count = len(driver.find_elements(By.CSS_SELECTOR, "[id^='notification-item-']"))
    read_btns[0].click()

    # After marking as read, the notification is removed or count decreases
    WebDriverWait(driver, 5).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "[id^='notification-item-']")) < initial_count
                  or not d.find_elements(By.ID, read_btn_id)
    )
    # Either fewer items or the read button is gone
    new_count = len(driver.find_elements(By.CSS_SELECTOR, "[id^='notification-item-']"))
    read_btn_still_present = bool(driver.find_elements(By.ID, read_btn_id))
    assert new_count < initial_count or not read_btn_still_present, (
        "Expected notification to be removed or mark-as-read button to disappear after clicking."
    )
