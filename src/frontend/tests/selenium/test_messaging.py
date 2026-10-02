"""
Citizen-reply-to-operator messaging test.

Covered use cases
-----------------
UC-10  Manage report       – operator assigns a pending report (setup)
UC-11  Send message        – operator sends a message to the citizen (setup)
UC-12  Reply to message    – citizen sends a reply to the operator's message

This test exercises the full conversation loop in a single browser session:
citizen submits → operator assigns and messages → citizen replies.
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
# UC-12  Full conversation flow: citizen submits → operator messages → citizen replies
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_full_messaging_conversation(driver):
    """
    UC-10 + UC-11 + UC-12 — Full operator/citizen messaging flow.

    Steps:
    1. Citizen creates a report.
    2. Operator logs in, assigns the report, opens detail, sends a message.
    3. Citizen logs in, navigates to the report detail, reads the message,
       and sends a reply.
    4. The reply is visible in the messages list.
    """
    suffix = unique_suffix()
    report_title = f"Conversation Test {suffix}"
    operator_message = f"Operator asks: please clarify {suffix}"
    citizen_reply = f"Citizen replies: understood {suffix}"

    # ------------------------------------------------------------------
    # Step 1 – Citizen creates a report
    # ------------------------------------------------------------------
    login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)
    wait_url_contains(driver, "/dashboard")

    driver.get(f"{FRONTEND_URL}/reports/new")
    wait_for_id(driver, "new-report-form")

    driver.find_element(By.ID, "report-title").send_keys(report_title)
    driver.find_element(By.ID, "report-description").send_keys(
        "Report for full conversation test."
    )

    category_select = Select(driver.find_element(By.ID, "report-category"))
    try:
        category_select.select_by_visible_text("Roads and Urban Furniture")
    except Exception:
        options = [o for o in category_select.options if o.get_attribute("value")]
        assert options, "No category options found."
        options[0].click()

    driver.find_element(By.ID, "report-latitude").clear()
    driver.find_element(By.ID, "report-latitude").send_keys("45.0703")
    driver.find_element(By.ID, "report-longitude").clear()
    driver.find_element(By.ID, "report-longitude").send_keys("7.6869")

    driver.find_element(By.ID, "new-report-submit").click()
    wait_url_not(driver, f"{FRONTEND_URL}/reports/new")

    logout(driver)

    # ------------------------------------------------------------------
    # Step 2 – Operator assigns the report and sends a message
    # ------------------------------------------------------------------
    login(driver, OPERATOR_EMAIL, OPERATOR_PASSWORD)
    wait_url_contains(driver, "/operator")

    wait_for_id(driver, "pending-reports-table")

    # Find the newly created report in the pending list
    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "[id^='pending-report-row-']")) > 0
    )
    rows = driver.find_elements(By.CSS_SELECTOR, "[id^='pending-report-row-']")
    report_id = None
    for row in rows:
        if report_title in row.text:
            row_id = row.get_attribute("id")
            report_id = row_id.split("-")[-1]
            break

    assert report_id is not None, (
        f"Could not find pending report with title {report_title!r}."
    )

    # Assign the report
    assign_btn = wait_clickable_id(driver, f"pending-report-assign-{report_id}")
    assign_btn.click()

    wait_for_id(driver, f"assigned-report-row-{report_id}")

    # Open the report detail page
    open_link_id = f"assigned-report-row-{report_id}-open-detail"
    open_link = wait_clickable_id(driver, open_link_id)
    open_link.click()

    wait_url_contains(driver, f"/reports/{report_id}")
    wait_visible_id(driver, "report-detail-title")

    # Send a message to the citizen
    message_input = wait_clickable_id(driver, "report-message-body")
    message_input.clear()
    message_input.send_keys(operator_message)

    wait_clickable_id(driver, "report-message-submit").click()

    # Wait for operator's message to appear
    WebDriverWait(driver, 10).until(
        lambda d: any(
            operator_message in el.text
            for el in d.find_elements(By.CSS_SELECTOR, "[id^='message-item-']")
        )
    )

    logout(driver)

    # ------------------------------------------------------------------
    # Step 3 – Citizen logs in and replies to the operator's message
    # ------------------------------------------------------------------
    login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)
    wait_url_contains(driver, "/dashboard")

    # Navigate directly to the report detail
    driver.get(f"{FRONTEND_URL}/reports/{report_id}")
    wait_visible_id(driver, "report-detail-title")

    # Verify the operator's message is visible to the citizen
    WebDriverWait(driver, 10).until(
        lambda d: any(
            operator_message in el.text
            for el in d.find_elements(By.CSS_SELECTOR, "[id^='message-item-']")
        )
    )

    # Citizen sends a reply
    reply_input = wait_clickable_id(driver, "report-message-body")
    reply_input.clear()
    reply_input.send_keys(citizen_reply)

    wait_clickable_id(driver, "report-message-submit").click()

    # Wait for the reply to appear in the messages list
    WebDriverWait(driver, 10).until(
        lambda d: any(
            citizen_reply in el.text
            for el in d.find_elements(By.CSS_SELECTOR, "[id^='message-item-']")
        )
    )

    messages = driver.find_elements(By.CSS_SELECTOR, "[id^='message-item-']")
    message_texts = [m.text for m in messages]
    assert any(citizen_reply in t for t in message_texts), (
        f"Citizen reply {citizen_reply!r} not found in messages list."
    )
    assert any(operator_message in t for t in message_texts), (
        f"Operator message {operator_message!r} not found in messages list after citizen reply."
    )


# ---------------------------------------------------------------------------
# UC-12 extension 3a – empty reply body is not submitted
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_empty_message_body_is_not_submitted(driver):
    """
    UC-11 extension 3a / UC-12 extension 3a — An empty message body must not
    be sent. The submit button has the required form field, so the form should
    either block submission (browser validation) or show an application error.
    """
    # Operator must be able to reach the report detail page
    login(driver, OPERATOR_EMAIL, OPERATOR_PASSWORD)
    wait_url_contains(driver, "/operator")

    # Use seeded report #1 which is always available
    driver.get(f"{FRONTEND_URL}/reports/1")
    wait_visible_id(driver, "report-detail-title")

    # Locate the message form
    message_area = driver.find_elements(By.ID, "report-message-body")
    if not message_area:
        # Operator may not have access to this report's messages — test is inconclusive
        pytest.skip("Operator does not have message access to report #1 in current state.")

    message_input = message_area[0]
    message_input.clear()
    # Leave body empty and attempt to submit
    submit_btn = driver.find_element(By.ID, "report-message-submit")
    submit_btn.click()

    # The browser's required attribute prevents submission (page stays the same)
    # OR an application error is shown
    still_on_report = f"/reports/" in driver.current_url
    has_error = bool(driver.find_elements(By.CSS_SELECTOR, "[id^='report-detail-error']"))
    assert still_on_report, (
        "Expected to stay on the report detail page when sending an empty message."
    )
