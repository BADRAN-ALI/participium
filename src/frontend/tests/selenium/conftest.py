"""
Shared fixtures and helpers for the Selenium acceptance test suite.

All tests interact with the running application through the browser;
no React internals, cookies, or database state are accessed directly.
"""

import uuid

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select

# ---------------------------------------------------------------------------
# Application URLs (default local dev configuration)
# ---------------------------------------------------------------------------

FRONTEND_URL = "http://localhost:5173"

# ---------------------------------------------------------------------------
# Seeded demo accounts
# ---------------------------------------------------------------------------

CITIZEN_EMAIL = "citizen@example.com"
CITIZEN_PASSWORD = "Citizen123!"

OPERATOR_EMAIL = "operator@example.com"
OPERATOR_PASSWORD = "Operator123!"

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Admin123!"

# ---------------------------------------------------------------------------
# Driver fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def driver():
    """Provide a headless Chrome WebDriver for a single test and close it after."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-gpu")
    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(0)
    yield drv
    drv.quit()


# ---------------------------------------------------------------------------
# Explicit wait helpers
# ---------------------------------------------------------------------------


def wait_for_id(driver, element_id, timeout=10):
    """Wait until an element with the given id is present in the DOM."""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, element_id))
    )


def wait_visible_id(driver, element_id, timeout=10):
    """Wait until an element with the given id is visible."""
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.ID, element_id))
    )


def wait_clickable_id(driver, element_id, timeout=10):
    """Wait until an element with the given id is clickable."""
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.ID, element_id))
    )


def wait_url_contains(driver, fragment, timeout=10):
    """Wait until the current URL contains fragment."""
    WebDriverWait(driver, timeout).until(EC.url_contains(fragment))


def wait_url_not(driver, url, timeout=10):
    """Wait until the current URL no longer equals url."""
    WebDriverWait(driver, timeout).until_not(EC.url_to_be(url))


# ---------------------------------------------------------------------------
# Application-level helpers
# ---------------------------------------------------------------------------


def login(driver, email, password):
    """
    Navigate to /login, enter credentials and submit.
    Waits until the browser navigates away from the login page.
    """
    driver.get(f"{FRONTEND_URL}/login")
    identifier_input = wait_clickable_id(driver, "login-identifier")
    identifier_input.clear()
    identifier_input.send_keys(email)

    password_input = driver.find_element(By.ID, "login-password")
    password_input.clear()
    password_input.send_keys(password)

    driver.find_element(By.ID, "login-submit").click()

    # Wait for redirect away from login
    wait_url_not(driver, f"{FRONTEND_URL}/login")


def logout(driver):
    """Click the logout button and wait for the login nav link to reappear."""
    btn = wait_clickable_id(driver, "logout-button")
    btn.click()
    wait_for_id(driver, "nav-login")


def unique_suffix():
    """Return an 8-character unique hex string for generating unique test data."""
    return uuid.uuid4().hex[:8]
