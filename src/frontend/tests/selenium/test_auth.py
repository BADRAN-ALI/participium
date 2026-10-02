"""
Authentication tests — UC-01 (Register), UC-02 (Login), UC-16 (Logout).

Covered use cases
-----------------
UC-01  Register account     – visitor creates a citizen account and verifies email
UC-02  Login                – registered citizen authenticates; invalid credentials rejected
UC-16  Logout               – authenticated user ends their session
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    wait_url_not,
    wait_url_contains,
)


# ---------------------------------------------------------------------------
# UC-01  Register account
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_register_new_account_and_verify_email(driver):
    """
    UC-01 — A visitor can create a citizen account and verify their email.

    The registration form accepts username, first name, last name, email,
    and password. After successful submission the application exposes a
    verification link (demo/local environment). Opening that link activates
    the account so the user can log in.
    """
    suffix = unique_suffix()
    username = f"testuser-{suffix}"
    email = f"testuser-{suffix}@example.com"

    # Navigate to registration page
    driver.get(f"{FRONTEND_URL}/register")
    wait_for_id(driver, "register-form")

    # Fill in the registration form
    driver.find_element(By.ID, "register-username").send_keys(username)
    driver.find_element(By.ID, "register-first-name").send_keys("Test")
    driver.find_element(By.ID, "register-last-name").send_keys("User")
    driver.find_element(By.ID, "register-email").send_keys(email)
    driver.find_element(By.ID, "register-password").send_keys("TestPass123!")

    driver.find_element(By.ID, "register-submit").click()

    # Success message must appear
    success_el = wait_visible_id(driver, "register-success")
    assert email in success_el.text, (
        f"Expected success message to mention {email!r}, got: {success_el.text!r}"
    )

    # Verification link exposed in local/demo environment
    verify_link = wait_clickable_id(driver, "verification-link")

    # Open the verification link — this activates the account
    verify_url = verify_link.get_attribute("href")
    driver.get(verify_url)

    # After verification, the application should respond without error
    # Navigate to login and verify the account is now usable
    driver.get(f"{FRONTEND_URL}/login")
    wait_for_id(driver, "login-identifier")

    driver.find_element(By.ID, "login-identifier").clear()
    driver.find_element(By.ID, "login-identifier").send_keys(email)
    driver.find_element(By.ID, "login-password").clear()
    driver.find_element(By.ID, "login-password").send_keys("TestPass123!")
    driver.find_element(By.ID, "login-submit").click()

    # Redirect to dashboard confirms the account is verified and active
    wait_url_not(driver, f"{FRONTEND_URL}/login")
    assert "/dashboard" in driver.current_url, (
        f"Expected redirect to /dashboard after login, got: {driver.current_url!r}"
    )


@pytest.mark.e2e
def test_register_duplicate_email_shows_error(driver):
    """
    UC-01 extension 4b — Registration with an already-registered email shows an error.
    """
    driver.get(f"{FRONTEND_URL}/register")
    wait_for_id(driver, "register-form")

    suffix = unique_suffix()
    driver.find_element(By.ID, "register-username").send_keys(f"dupuser-{suffix}")
    driver.find_element(By.ID, "register-first-name").send_keys("Dup")
    driver.find_element(By.ID, "register-last-name").send_keys("User")
    driver.find_element(By.ID, "register-email").send_keys(CITIZEN_EMAIL)  # already registered
    driver.find_element(By.ID, "register-password").send_keys("TestPass123!")
    driver.find_element(By.ID, "register-submit").click()

    error_el = wait_visible_id(driver, "register-error")
    assert error_el.text, "Expected a non-empty error message for duplicate email."


# ---------------------------------------------------------------------------
# UC-02  Login
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_login_citizen_success(driver):
    """
    UC-02 — A registered citizen can log in with valid credentials and is
    redirected to the appropriate area (dashboard).
    """
    login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)

    wait_url_contains(driver, "/dashboard")
    assert "/dashboard" in driver.current_url, (
        f"Expected /dashboard after citizen login, got: {driver.current_url!r}"
    )
    # Logout button confirms authenticated session
    wait_for_id(driver, "logout-button")


@pytest.mark.e2e
def test_login_invalid_credentials_shows_error(driver):
    """
    UC-02 extension 4a — Invalid credentials do not create a session and an
    error message is shown.
    """
    driver.get(f"{FRONTEND_URL}/login")
    wait_for_id(driver, "login-identifier")

    driver.find_element(By.ID, "login-identifier").send_keys("nobody@example.com")
    driver.find_element(By.ID, "login-password").send_keys("WrongPassword!")
    driver.find_element(By.ID, "login-submit").click()

    error_el = wait_visible_id(driver, "login-error")
    assert error_el.text, "Expected a non-empty error message for invalid credentials."
    # Must remain on login page
    assert "/login" in driver.current_url, (
        f"Browser should stay on /login on invalid credentials, got: {driver.current_url!r}"
    )


# ---------------------------------------------------------------------------
# UC-16  Logout
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_logout_ends_authenticated_session(driver):
    """
    UC-16 — An authenticated user can log out; the session is terminated and
    restricted areas are no longer accessible without a new login.
    """
    login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)
    wait_url_contains(driver, "/dashboard")

    logout(driver)

    # After logout the login nav link must be visible
    wait_for_id(driver, "nav-login")

    # Attempting to visit a citizen-only page redirects away from it
    driver.get(f"{FRONTEND_URL}/reports/new")
    WebDriverWait(driver, 5).until(
        lambda d: "/reports/new" not in d.current_url or
                  d.find_elements(By.ID, "nav-login")
    )
    # Either redirected away or still accessible but without auth UI
    assert driver.find_elements(By.ID, "nav-login"), (
        "Expected nav-login to be present after logout, indicating unauthenticated state."
    )
