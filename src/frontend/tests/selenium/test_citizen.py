"""
Citizen workflow tests.

Covered use cases
-----------------
UC-03  Submit report          – authenticated citizen creates a geo-located report
UC-07  Follow / Unfollow      – citizen follows and unfollows a report by another user
UC-15  Manage citizen profile – citizen updates profile preferences
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
# UC-03  Submit report
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_citizen_can_submit_report(driver):
    """
    UC-03 — An authenticated citizen can fill in the report submission form
    (title, description, category, latitude, longitude) and submit a new
    report. After submission the report appears in the citizen's dashboard.
    """
    suffix = unique_suffix()
    report_title = f"Selenium Test Report {suffix}"

    login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)

    # Navigate to new report page via the nav link
    nav_link = wait_clickable_id(driver, "nav-new-report")
    nav_link.click()
    wait_url_contains(driver, "/reports/new")

    # Fill in the form
    wait_for_id(driver, "new-report-form")
    driver.find_element(By.ID, "report-title").send_keys(report_title)
    driver.find_element(By.ID, "report-description").send_keys(
        "Automated Selenium test report — safe to ignore."
    )

    # Select a category from the dropdown (choose the first available option)
    category_select = Select(driver.find_element(By.ID, "report-category"))
    # The first option is a placeholder; select the first actual category
    options = category_select.options
    category_options = [o for o in options if o.get_attribute("value")]
    assert category_options, "Expected at least one category option in the report-category select."
    category_options[0].click()

    # Set coordinates directly in the latitude/longitude inputs
    lat_input = driver.find_element(By.ID, "report-latitude")
    lat_input.clear()
    lat_input.send_keys("45.0703")

    lng_input = driver.find_element(By.ID, "report-longitude")
    lng_input.clear()
    lng_input.send_keys("7.6869")

    driver.find_element(By.ID, "new-report-submit").click()

    # After successful submission the page should navigate away from /reports/new
    wait_url_not(driver, f"{FRONTEND_URL}/reports/new")

    # Verify the new report appears in the citizen's dashboard report list
    driver.get(f"{FRONTEND_URL}/dashboard")
    wait_for_id(driver, "my-reports-table")

    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "[id^='my-report-row-']")) > 0
    )
    rows = driver.find_elements(By.CSS_SELECTOR, "[id^='my-report-row-']")
    titles = [r.text for r in rows]
    assert any(report_title in t for t in titles), (
        f"Expected new report title {report_title!r} to appear in dashboard report list."
    )


@pytest.mark.e2e
def test_submit_report_requires_title_field(driver):
    """
    UC-03 extension 6a — Missing required fields prevent submission.
    The title field is required and its absence triggers a browser validation
    or an application error.
    """
    login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)

    driver.get(f"{FRONTEND_URL}/reports/new")
    wait_for_id(driver, "new-report-form")

    # Fill category and coordinates but intentionally omit title
    category_select = Select(driver.find_element(By.ID, "report-category"))
    options = [o for o in category_select.options if o.get_attribute("value")]
    if options:
        options[0].click()

    driver.find_element(By.ID, "report-latitude").clear()
    driver.find_element(By.ID, "report-latitude").send_keys("45.0703")
    driver.find_element(By.ID, "report-longitude").clear()
    driver.find_element(By.ID, "report-longitude").send_keys("7.6869")

    driver.find_element(By.ID, "new-report-submit").click()

    # The browser enforces the required attribute so we should stay on the same page
    # OR the app renders an error element
    still_on_new_report = "/reports/new" in driver.current_url
    has_error = bool(driver.find_elements(By.ID, "new-report-error"))
    assert still_on_new_report or has_error, (
        "Expected to stay on /reports/new or see an error when title is missing."
    )


# ---------------------------------------------------------------------------
# UC-07  Follow / Unfollow report
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_citizen_can_follow_and_unfollow_a_report(driver):
    """
    UC-07 — An authenticated citizen can follow a report and then unfollow it.

    The test registers a fresh citizen account (to ensure no prior follow state),
    then follows seeded report #1. After confirming the follow, the same button
    is used to unfollow, and the state reverts.
    """
    suffix = unique_suffix()
    username = f"follower-{suffix}"
    email = f"follower-{suffix}@example.com"
    password = "TestPass123!"

    # Register a fresh account so there is no prior follow relationship
    driver.get(f"{FRONTEND_URL}/register")
    wait_for_id(driver, "register-form")
    driver.find_element(By.ID, "register-username").send_keys(username)
    driver.find_element(By.ID, "register-first-name").send_keys("Follow")
    driver.find_element(By.ID, "register-last-name").send_keys("Tester")
    driver.find_element(By.ID, "register-email").send_keys(email)
    driver.find_element(By.ID, "register-password").send_keys(password)
    driver.find_element(By.ID, "register-submit").click()

    # Verify the new account via the exposed link
    verify_link = wait_clickable_id(driver, "verification-link")
    verify_url = verify_link.get_attribute("href")
    driver.get(verify_url)

    # Log in as the new citizen
    login(driver, email, password)
    wait_url_contains(driver, "/dashboard")

    # Open the detail page of seeded report #1 (submitted by the seeded citizen account)
    driver.get(f"{FRONTEND_URL}/reports/1")
    wait_visible_id(driver, "report-detail-title")

    # Follow button must be present
    follow_btn = wait_clickable_id(driver, "follow-button")
    initial_text = follow_btn.text.strip()

    follow_btn.click()

    # After clicking, the button text changes to indicate the new state
    WebDriverWait(driver, 10).until(
        lambda d: d.find_element(By.ID, "follow-button").text.strip() != initial_text
    )
    after_click_text = driver.find_element(By.ID, "follow-button").text.strip()
    assert after_click_text != initial_text, (
        "Expected follow-button text to change after clicking."
    )

    # Click again to toggle back (unfollow)
    driver.find_element(By.ID, "follow-button").click()

    WebDriverWait(driver, 10).until(
        lambda d: d.find_element(By.ID, "follow-button").text.strip() == initial_text
    )
    restored_text = driver.find_element(By.ID, "follow-button").text.strip()
    assert restored_text == initial_text, (
        "Expected follow-button text to return to its initial state after unfollowing."
    )


# ---------------------------------------------------------------------------
# UC-15  Manage citizen profile
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_citizen_can_update_profile_username(driver):
    """
    UC-15 — An authenticated citizen can update their username from the
    profile form on the dashboard page and receive a success confirmation.
    """
    login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)
    wait_url_contains(driver, "/dashboard")

    # Navigate to dashboard where the profile form lives
    driver.get(f"{FRONTEND_URL}/dashboard")
    wait_for_id(driver, "profile-form")

    # Update username to its current value + a unique suffix (idempotent)
    username_input = wait_clickable_id(driver, "profile-username")
    current_username = username_input.get_attribute("value")
    suffix = unique_suffix()
    new_username = f"citizen-{suffix}"

    username_input.clear()
    username_input.send_keys(new_username)

    driver.find_element(By.ID, "profile-save").click()

    # Success message must appear
    success_el = wait_visible_id(driver, "profile-success")
    assert success_el.text, "Expected a non-empty success message after profile update."

    # Reset back to original username so other tests are not affected
    username_input = driver.find_element(By.ID, "profile-username")
    username_input.clear()
    username_input.send_keys(current_username)
    driver.find_element(By.ID, "profile-save").click()
    wait_visible_id(driver, "profile-success")


@pytest.mark.e2e
def test_citizen_can_toggle_email_notification_preference(driver):
    """
    UC-15 — A citizen can toggle the email-notifications checkbox and save;
    a success confirmation is shown.
    """
    login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)

    driver.get(f"{FRONTEND_URL}/dashboard")
    wait_for_id(driver, "profile-form")

    checkbox = wait_clickable_id(driver, "profile-email-notifications")
    initial_state = checkbox.is_selected()

    # Toggle the checkbox
    checkbox.click()
    driver.find_element(By.ID, "profile-save").click()

    success_el = wait_visible_id(driver, "profile-success")
    assert success_el.text, "Expected success message after saving email notification preference."

    # Restore original state
    checkbox = driver.find_element(By.ID, "profile-email-notifications")
    if checkbox.is_selected() != initial_state:
        checkbox.click()
        driver.find_element(By.ID, "profile-save").click()
        wait_visible_id(driver, "profile-success")
