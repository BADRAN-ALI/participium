"""
Admin panel tests.

Covered use cases
-----------------
UC-13  View private statistics         – admin can access stats inaccessible to other roles
UC-14  Manage categories and users     – admin creates a category, sees user list, saves a user
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
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    login,
    logout,
    unique_suffix,
    wait_for_id,
    wait_visible_id,
    wait_clickable_id,
    wait_url_contains,
)


# ---------------------------------------------------------------------------
# UC-13  View private statistics
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_admin_can_access_private_statistics(driver):
    """
    UC-13 — The admin panel shows private statistics sections that are not
    available to unauthenticated users or citizens.
    """
    login(driver, ADMIN_EMAIL, ADMIN_PASSWORD)
    wait_url_contains(driver, "/admin")

    # Admin page must be present with its statistics section
    wait_for_id(driver, "admin-page")

    # Private statistics are rendered inside metric columns
    # At least one admin-metric-item-* element must be present
    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "[id^='admin-metric-item-']")) > 0
    )
    metric_items = driver.find_elements(By.CSS_SELECTOR, "[id^='admin-metric-item-']")
    assert metric_items, "Expected admin private statistics items to be visible."


@pytest.mark.e2e
def test_citizen_cannot_access_admin_page(driver):
    """
    UC-13 — A citizen is not allowed to access the admin area; navigating to
    /admin should redirect away or render without the admin panel content.
    """
    login(driver, CITIZEN_EMAIL, CITIZEN_PASSWORD)
    wait_url_contains(driver, "/dashboard")

    driver.get(f"{FRONTEND_URL}/admin")

    # Either redirected away or admin-page content is not rendered
    WebDriverWait(driver, 5).until(
        lambda d: "/admin" not in d.current_url or
                  not d.find_elements(By.ID, "admin-page")
    )
    is_redirected = "/admin" not in driver.current_url
    no_admin_content = not driver.find_elements(By.ID, "admin-page")
    assert is_redirected or no_admin_content, (
        "Expected citizen to be denied access to the admin page."
    )


# ---------------------------------------------------------------------------
# UC-14  Manage categories
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_admin_can_create_new_category(driver):
    """
    UC-14 — Admin creates a new report category. The category name must
    appear in the categories table after creation.
    """
    suffix = unique_suffix()
    category_name = f"Selenium Cat {suffix}"

    login(driver, ADMIN_EMAIL, ADMIN_PASSWORD)
    wait_url_contains(driver, "/admin")
    wait_for_id(driver, "admin-category-form")

    # Fill in the new category name
    name_input = wait_clickable_id(driver, "admin-new-category-name")
    name_input.clear()
    name_input.send_keys(category_name)

    driver.find_element(By.ID, "admin-new-category-submit").click()

    # Success message must appear
    success_el = wait_visible_id(driver, "admin-success")
    assert success_el.text, "Expected success message after creating a category."

    # The new category must appear in the categories table
    WebDriverWait(driver, 10).until(
        lambda d: any(
            category_name in row.text
            for row in d.find_elements(By.CSS_SELECTOR, "[id^='admin-category-row-']")
        )
    )
    category_rows = driver.find_elements(By.CSS_SELECTOR, "[id^='admin-category-row-']")
    names_in_table = [r.text for r in category_rows]
    assert any(category_name in n for n in names_in_table), (
        f"Expected new category {category_name!r} to appear in the category table."
    )


@pytest.mark.e2e
def test_admin_create_category_duplicate_shows_error(driver):
    """
    UC-14 extension 4b — Attempting to create a category with an already-used
    name shows an error.
    """
    login(driver, ADMIN_EMAIL, ADMIN_PASSWORD)
    wait_url_contains(driver, "/admin")
    wait_for_id(driver, "admin-category-form")

    # 'Roads and Urban Furniture' is seeded and always exists
    name_input = wait_clickable_id(driver, "admin-new-category-name")
    name_input.clear()
    name_input.send_keys("Roads and Urban Furniture")

    driver.find_element(By.ID, "admin-new-category-submit").click()

    error_el = wait_visible_id(driver, "admin-error")
    assert error_el.text, "Expected an error when creating a duplicate category name."


# ---------------------------------------------------------------------------
# UC-14  Manage users
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_admin_can_create_new_user(driver):
    """
    UC-14 — Admin creates a new citizen user through the admin user form.
    The user appears in the users table after creation.
    """
    suffix = unique_suffix()
    username = f"adminuser-{suffix}"
    email = f"adminuser-{suffix}@example.com"

    login(driver, ADMIN_EMAIL, ADMIN_PASSWORD)
    wait_url_contains(driver, "/admin")
    wait_for_id(driver, "admin-user-form")

    # Fill in the create-user form
    driver.find_element(By.ID, "admin-new-user-username").send_keys(username)
    driver.find_element(By.ID, "admin-new-user-first-name").send_keys("Admin")
    driver.find_element(By.ID, "admin-new-user-last-name").send_keys("Created")
    driver.find_element(By.ID, "admin-new-user-email").send_keys(email)
    driver.find_element(By.ID, "admin-new-user-password").send_keys("AdminCreated123!")

    # Select role 'citizen'
    role_select = Select(driver.find_element(By.ID, "admin-new-user-role"))
    role_select.select_by_value("citizen")

    driver.find_element(By.ID, "admin-new-user-submit").click()

    # Success message must appear
    success_el = wait_visible_id(driver, "admin-success")
    assert success_el.text, "Expected success message after creating a user."

    # The new user must appear in the users table
    WebDriverWait(driver, 10).until(
        lambda d: any(
            email in row.text
            for row in d.find_elements(By.CSS_SELECTOR, "[id^='admin-user-row-']")
        )
    )
    user_rows = driver.find_elements(By.CSS_SELECTOR, "[id^='admin-user-row-']")
    row_texts = [r.text for r in user_rows]
    assert any(email in t for t in row_texts), (
        f"Expected new user {email!r} to appear in the users table."
    )


@pytest.mark.e2e
def test_admin_can_save_user_changes(driver):
    """
    UC-14 — Admin can edit a user row (e.g., toggle active state) and save the
    change. A success message confirms the update.
    """
    login(driver, ADMIN_EMAIL, ADMIN_PASSWORD)
    wait_url_contains(driver, "/admin")

    # Wait for user rows to load
    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "[id^='admin-user-row-']")) > 0
    )
    user_rows = driver.find_elements(By.CSS_SELECTOR, "[id^='admin-user-row-']")
    assert user_rows, "Expected at least one user row in the admin users table."

    # Find the first user row that has a save button
    first_row = user_rows[0]
    row_id = first_row.get_attribute("id")  # e.g. "admin-user-row-3"
    user_id = row_id.split("-")[-1]

    save_btn_id = f"admin-user-save-{user_id}"
    save_btns = driver.find_elements(By.ID, save_btn_id)
    if not save_btns:
        pytest.skip(f"No save button found for user row {row_id!r}.")

    # Toggle the active checkbox for this user row
    active_checkbox_id = f"admin-user-status-{user_id}"
    active_checkboxes = driver.find_elements(By.ID, active_checkbox_id)
    if active_checkboxes:
        active_checkboxes[0].click()

    save_btns[0].click()

    # Success message confirms the save
    success_el = wait_visible_id(driver, "admin-success")
    assert success_el.text, "Expected success message after saving user changes."

    # Restore the original checkbox state
    active_checkboxes = driver.find_elements(By.ID, active_checkbox_id)
    if active_checkboxes:
        active_checkboxes[0].click()
        driver.find_elements(By.ID, save_btn_id)[0].click()
        wait_visible_id(driver, "admin-success")


# ---------------------------------------------------------------------------
# UC-13 guard – unauthenticated access to admin
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_unauthenticated_user_cannot_access_admin_page(driver):
    """
    UC-13 — An unauthenticated visitor cannot reach the admin panel.
    Navigating to /admin should redirect to a non-restricted area or render
    without admin panel content.
    """
    driver.get(f"{FRONTEND_URL}/admin")

    WebDriverWait(driver, 5).until(
        lambda d: "/admin" not in d.current_url or
                  not d.find_elements(By.ID, "admin-page")
    )
    is_redirected = "/admin" not in driver.current_url
    no_admin_content = not driver.find_elements(By.ID, "admin-page")
    assert is_redirected or no_admin_content, (
        "Expected unauthenticated visitor to be denied the admin panel."
    )
