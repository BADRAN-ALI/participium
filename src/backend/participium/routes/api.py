from __future__ import annotations

from typing import Any

from flask import Blueprint, Response, current_app, jsonify, request

from participium.config.constants import PUBLIC_VISIBLE_STATUSES
from participium.container import get_controllers
from participium.core.auth import current_user, login_required, login_user, logout_user, roles_required
from participium.core.exceptions import ValidationError
from participium.core.serialization import (
    serialize_category,
    serialize_message,
    serialize_notification,
    serialize_report_detail,
    serialize_report_summary,
    serialize_user,
)
from participium.core.utils import build_csv, parse_date
from participium.models.enums import ReportStatus, Role

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


def _payload() -> dict[str, Any]:
    return request.get_json(silent=True) or request.form.to_dict()


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_report_status(status_value: str | None) -> ReportStatus | None:
    if not status_value:
        return None
    try:
        return ReportStatus(status_value)
    except ValueError as exc:
        raise ValidationError("Invalid report status filter.") from exc


def _report_filters() -> dict[str, Any]:
    status_value = request.args.get("status")
    return {
        "category_id": request.args.get("category_id", type=int),
        "status": _parse_report_status(status_value),
        "date_from": parse_date(request.args.get("date_from")),
        "date_to": parse_date(request.args.get("date_to")),
        "sort": request.args.get("sort", "desc"),
    }


@api_bp.get("/health")
def health_check():
    """
    Health check endpoint.
    ---
    tags:
      - System
    responses:
      200:
        description: Service is available.
        schema:
          $ref: '#/definitions/Health'
    """
    return jsonify({"status": "ok"})




@api_bp.get("/meta/reference-data")
def reference_data_api():
    """
    Retrieve static reference data needed by the frontend.
    ---
    tags:
      - System
    responses:
      200:
        description: Reference data.
        schema:
          $ref: '#/definitions/ReferenceData'
    """
    return jsonify(
        {
            "roles": [role.value for role in Role],
            "report_statuses": [status.value for status in ReportStatus],
            "public_report_statuses": [status.value for status in PUBLIC_VISIBLE_STATUSES],
        }
    )

@api_bp.post("/auth/register")
def register_user_api():
    """
    Register a new citizen account.
    ---
    tags:
      - Authentication
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          $ref: '#/definitions/AuthRegisterRequest'
    responses:
      201:
        description: Account created.
        schema:
          $ref: '#/definitions/AuthRegisterResponse'
      400:
        description: Validation error.
        schema:
          $ref: '#/definitions/Error'
    """
    controllers = get_controllers()
    verification_template = request.url_root.rstrip("/") + "/api/v1/auth/verify"
    user, verification_url = controllers.auth.register(_payload(), verification_template)
    response_payload = {"user": serialize_user(user)}
    if current_app.config["SETTINGS"].expose_verification_links:
        response_payload["verification_url"] = verification_url
    return jsonify(response_payload), 201


@api_bp.get("/auth/verify/<token_value>")
def verify_email_api(token_value: str):
    """
    Verify a citizen email address.
    ---
    tags:
      - Authentication
    parameters:
      - in: path
        name: token_value
        type: string
        required: true
    responses:
      200:
        description: Email verified.
        schema:
          $ref: '#/definitions/AuthUserMessageResponse'
      400:
        description: Invalid or expired token.
        schema:
          $ref: '#/definitions/Error'
    """
    user = get_controllers().auth.verify_email(token_value)
    return jsonify({"message": "Email verified.", "user": serialize_user(user)})


@api_bp.post("/auth/login")
def login_api():
    """
    Log in with username or email and create a session cookie.
    ---
    tags:
      - Authentication
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          $ref: '#/definitions/AuthLoginRequest'
    responses:
      200:
        description: Logged in.
        schema:
          $ref: '#/definitions/AuthUserMessageResponse'
      401:
        description: Invalid credentials.
        schema:
          $ref: '#/definitions/Error'
    """
    payload = _payload()
    user = get_controllers().auth.login(payload.get("identifier", ""), payload.get("password", ""))
    login_user(user)
    return jsonify({"message": "Logged in.", "user": serialize_user(user)})


@api_bp.post("/auth/logout")
def logout_api():
    """
    Log out the current session.
    ---
    tags:
      - Authentication
    responses:
      200:
        description: Logged out.
        schema:
          $ref: '#/definitions/MessageOnlyResponse'
    """
    logout_user()
    return jsonify({"message": "Logged out."})


@api_bp.get("/categories")
def list_categories_api():
    """
    List active report categories.
    ---
    tags:
      - Categories
    responses:
      200:
        description: Category list.
        schema:
          type: array
          items:
            $ref: '#/definitions/Category'
    """
    categories = get_controllers().admin.list_categories(active_only=True)
    return jsonify([serialize_category(category) for category in categories])


@api_bp.get("/reports")
def list_reports_api():
    """
    List published reports with filters.
    ---
    tags:
      - Reports
    parameters:
      - in: query
        name: category_id
        type: integer
      - in: query
        name: status
        type: string
      - in: query
        name: date_from
        type: string
        format: date-time
      - in: query
        name: date_to
        type: string
        format: date-time
      - in: query
        name: sort
        type: string
        enum: [asc, desc]
    responses:
      200:
        description: Published reports.
        schema:
          type: array
          items:
            $ref: '#/definitions/ReportSummary'
      400:
        description: Invalid filters.
        schema:
          $ref: '#/definitions/Error'
    """
    filters = _report_filters()
    reports = get_controllers().reports.list_public_reports(
        category_id=filters["category_id"],
        status=filters["status"],
        date_from=filters["date_from"],
        date_to=filters["date_to"],
        sort=filters["sort"],
    )
    return jsonify([serialize_report_summary(report, viewer=current_user()) for report in reports])


@api_bp.post("/reports")
@login_required
@roles_required(Role.CITIZEN)
def create_report_api():
    """
    Create a new report with up to 3 photos.
    ---
    tags:
      - Reports
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: title
        type: string
        required: true
      - in: formData
        name: description
        type: string
        required: true
      - in: formData
        name: category_id
        type: integer
        required: true
      - in: formData
        name: latitude
        type: number
        required: true
      - in: formData
        name: longitude
        type: number
        required: true
      - in: formData
        name: is_anonymous
        type: boolean
      - in: formData
        name: photos
        type: file
        required: true
    responses:
      201:
        description: Report created.
        schema:
          $ref: '#/definitions/ReportDetail'
      400:
        description: Validation error.
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Citizen role required.
        schema:
          $ref: '#/definitions/Error'
    """
    form_data = request.form.to_dict()
    report = get_controllers().reports.create_report(
        reporter=current_user(),
        category_id=form_data.get("category_id"),
        title=form_data.get("title"),
        description=form_data.get("description"),
        latitude=form_data.get("latitude"),
        longitude=form_data.get("longitude"),
        photos=request.files.getlist("photos"),
        is_anonymous=_as_bool(form_data.get("is_anonymous"), False),
    )
    return jsonify(serialize_report_detail(report, viewer=current_user())), 201


@api_bp.get("/reports/export")
def export_reports_api():
    """
    Export the filtered published report list as CSV.
    ---
    tags:
      - Reports
    responses:
      200:
        description: CSV export.
        schema:
          type: string
    """
    filters = _report_filters()
    rows = get_controllers().reports.export_rows(
        category_id=filters["category_id"],
        status=filters["status"],
        date_from=filters["date_from"],
        date_to=filters["date_to"],
        sort=filters["sort"],
    )
    csv_content = build_csv(
        rows,
        ["id", "title", "category", "status", "created_at", "latitude", "longitude"],
    )
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=participium_reports.csv"},
    )


@api_bp.get("/reports/<int:report_id>")
def report_detail_api(report_id: int):
    """
    Retrieve a report detail page payload.
    ---
    tags:
      - Reports
    parameters:
      - in: path
        name: report_id
        type: integer
        required: true
    responses:
      200:
        description: Report detail.
        schema:
          $ref: '#/definitions/ReportDetail'
      403:
        description: Access denied.
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Report not found.
        schema:
          $ref: '#/definitions/Error'
    """
    detail_context = get_controllers().reports.build_detail_context(report_id, current_user())
    return jsonify(
        serialize_report_detail(
            detail_context.report,
            viewer=current_user(),
            include_messages=detail_context.can_access_messages,
        )
    )


@api_bp.post("/reports/<int:report_id>/follow")
@login_required
@roles_required(Role.CITIZEN)
def follow_report_api(report_id: int):
    """
    Follow a published report.
    ---
    tags:
      - Reports
    parameters:
      - in: path
        name: report_id
        type: integer
        required: true
    responses:
      200:
        description: Report followed.
        schema:
          $ref: '#/definitions/ReportDetail'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Citizen role required.
        schema:
          $ref: '#/definitions/Error'
    """
    report = get_controllers().reports.follow_report(report_id, current_user())
    return jsonify(serialize_report_detail(report, viewer=current_user()))


@api_bp.delete("/reports/<int:report_id>/follow")
@login_required
@roles_required(Role.CITIZEN)
def unfollow_report_api(report_id: int):
    """
    Unfollow a previously followed report.
    ---
    tags:
      - Reports
    parameters:
      - in: path
        name: report_id
        type: integer
        required: true
    responses:
      200:
        description: Report unfollowed.
        schema:
          $ref: '#/definitions/ReportDetail'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Citizen role required.
        schema:
          $ref: '#/definitions/Error'
    """
    report = get_controllers().reports.unfollow_report(report_id, current_user())
    return jsonify(serialize_report_detail(report, viewer=current_user()))


@api_bp.get("/reports/<int:report_id>/messages")
@login_required
def list_messages_api(report_id: int):
    """
    List messages for a report conversation.
    ---
    tags:
      - Messaging
    parameters:
      - in: path
        name: report_id
        type: integer
        required: true
    responses:
      200:
        description: Message thread.
        schema:
          type: array
          items:
            $ref: '#/definitions/Message'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Access denied.
        schema:
          $ref: '#/definitions/Error'
    """
    detail_context = get_controllers().reports.build_detail_context(report_id, current_user())
    messages = get_controllers().reports.list_messages(detail_context.report, current_user())
    return jsonify([serialize_message(message) for message in messages])


@api_bp.post("/reports/<int:report_id>/messages")
@login_required
def send_message_api(report_id: int):
    """
    Send a message on a report conversation.
    ---
    tags:
      - Messaging
    consumes:
      - application/json
    parameters:
      - in: path
        name: report_id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          $ref: '#/definitions/SendMessageRequest'
    responses:
      201:
        description: Message created.
        schema:
          $ref: '#/definitions/Message'
      400:
        description: Validation error.
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Access denied.
        schema:
          $ref: '#/definitions/Error'
    """
    detail_context = get_controllers().reports.build_detail_context(report_id, current_user())
    message = get_controllers().reports.send_message(
        detail_context.report,
        current_user(),
        _payload().get("body", ""),
    )
    return jsonify(serialize_message(message)), 201


@api_bp.get("/stats/public")
def public_stats_api():
    """
    Retrieve public statistics for published reports.
    ---
    tags:
      - Statistics
    parameters:
      - in: query
        name: granularity
        type: string
        enum: [day, week, month]
    responses:
      200:
        description: Public statistics.
        schema:
          $ref: '#/definitions/Statistics'
      400:
        description: Invalid granularity.
        schema:
          $ref: '#/definitions/Error'
    """
    granularity = request.args.get("granularity", "day")
    return jsonify(get_controllers().statistics.public_statistics(granularity))


@api_bp.get("/users/me")
@login_required
def me_api():
    """
    Retrieve the current authenticated user profile.
    ---
    tags:
      - Users
    responses:
      200:
        description: Current user.
        schema:
          $ref: '#/definitions/User'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
    """
    return jsonify(serialize_user(current_user()))


@api_bp.put("/users/me")
@login_required
def update_me_api():
    """
    Update the current authenticated user profile.
    ---
    tags:
      - Users
    consumes:
      - multipart/form-data
    responses:
      200:
        description: Updated profile.
        schema:
          $ref: '#/definitions/User'
      400:
        description: Validation error.
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
    """
    payload = _payload()
    if request.form:
        payload["email_notifications_enabled"] = "email_notifications_enabled" in request.form
    elif "email_notifications_enabled" in payload:
        payload["email_notifications_enabled"] = _as_bool(payload.get("email_notifications_enabled"))
    user = get_controllers().users.update_profile(
        user=current_user(),
        username=payload.get("username"),
        first_name=payload.get("first_name"),
        last_name=payload.get("last_name"),
        email_notifications_enabled=payload.get("email_notifications_enabled"),
        profile_picture=request.files.get("profile_picture"),
    )
    return jsonify(serialize_user(user))


@api_bp.delete("/users/me")
@login_required
def delete_me_api():
    """
    Delete the current authenticated account and personal data.
    ---
    tags:
      - Users
    responses:
      200:
        description: Account deleted.
        schema:
          $ref: '#/definitions/MessageOnlyResponse'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
    """
    get_controllers().users.delete_account(current_user())
    logout_user()
    return jsonify({"message": "Account deleted."})


@api_bp.get("/users/me/reports")
@login_required
def my_reports_api():
    """
    List reports created by the current user.
    ---
    tags:
      - Users
    responses:
      200:
        description: User reports.
        schema:
          type: array
          items:
            $ref: '#/definitions/ReportSummary'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
    """
    reports = get_controllers().reports.list_user_reports(current_user())
    return jsonify([serialize_report_summary(report, viewer=current_user()) for report in reports])


@api_bp.get("/users/me/notifications")
@login_required
def my_notifications_api():
    """
    List notifications for the current user.
    ---
    tags:
      - Users
    responses:
      200:
        description: Notifications.
        schema:
          type: array
          items:
            $ref: '#/definitions/Notification'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
    """
    notifications = get_controllers().users.list_notifications(current_user().id)
    return jsonify([serialize_notification(item) for item in notifications])


@api_bp.post("/users/me/notifications/<int:notification_id>/read")
@login_required
def mark_notification_read_api(notification_id: int):
    """
    Mark a notification as read.
    ---
    tags:
      - Users
    parameters:
      - in: path
        name: notification_id
        type: integer
        required: true
    responses:
      200:
        description: Notification updated.
        schema:
          $ref: '#/definitions/Notification'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Notification not found.
        schema:
          $ref: '#/definitions/Error'
    """
    controllers = get_controllers()
    notification = controllers.users.get_notification_for_user(current_user().id, notification_id)
    notification = controllers.users.mark_notification_as_read(notification)
    return jsonify(serialize_notification(notification))


@api_bp.get("/operator/reports/pending")
@login_required
@roles_required(Role.ADMIN, Role.OPERATOR)
def pending_reports_api():
    """
    List reports waiting for approval.
    ---
    tags:
      - Operator
    responses:
      200:
        description: Pending reports.
        schema:
          type: array
          items:
            $ref: '#/definitions/ReportSummary'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Operator or admin role required.
        schema:
          $ref: '#/definitions/Error'
    """
    dashboard_context = get_controllers().operators.build_dashboard(current_user(), _report_filters())
    return jsonify([serialize_report_summary(report, viewer=current_user()) for report in dashboard_context.pending_reports])


@api_bp.get("/operator/reports/assigned")
@login_required
@roles_required(Role.ADMIN, Role.OPERATOR)
def assigned_reports_api():
    """
    List operator-visible reports.
    ---
    tags:
      - Operator
    responses:
      200:
        description: Operator report queue.
        schema:
          type: array
          items:
            allOf:
              - $ref: '#/definitions/ReportSummary'
              - type: object
                properties:
                  unread_message_count:
                    type: integer
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Operator or admin role required.
        schema:
          $ref: '#/definitions/Error'
    """
    dashboard_context = get_controllers().operators.build_dashboard(current_user(), _report_filters())
    return jsonify(
        [
            {
                **serialize_report_summary(report, viewer=current_user()),
                "unread_message_count": dashboard_context.unread_message_counts.get(report.id, 0),
            }
            for report in dashboard_context.assigned_reports
        ]
    )


@api_bp.post("/operator/reports/<int:report_id>/assign")
@login_required
@roles_required(Role.ADMIN, Role.OPERATOR)
def assign_report_api(report_id: int):
    """
    Accept a pending report for handling in its category.
    ---
    tags:
      - Operator
    parameters:
      - in: path
        name: report_id
        type: integer
        required: true
    responses:
      200:
        description: Report assigned.
        schema:
          $ref: '#/definitions/ReportDetail'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Operator or admin role required.
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Report not found.
        schema:
          $ref: '#/definitions/Error'
    """
    report = get_controllers().operators.assign_report(report_id, current_user())
    return jsonify(serialize_report_detail(report, viewer=current_user()))


@api_bp.post("/operator/reports/<int:report_id>/status")
@login_required
@roles_required(Role.ADMIN, Role.OPERATOR)
def update_report_status_api(report_id: int):
    """
    Update the status of a report.
    ---
    tags:
      - Operator
    parameters:
      - in: path
        name: report_id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          $ref: '#/definitions/UpdateStatusRequest'
    responses:
      200:
        description: Status updated.
        schema:
          $ref: '#/definitions/ReportDetail'
      400:
        description: Validation error.
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Operator or admin role required.
        schema:
          $ref: '#/definitions/Error'
    """
    payload = _payload()
    report = get_controllers().operators.update_status(
        report_id,
        current_user(),
        payload.get("status", ""),
        payload.get("note"),
    )
    return jsonify(serialize_report_detail(report, viewer=current_user()))


@api_bp.get("/admin/users")
@login_required
@roles_required(Role.ADMIN)
def admin_users_api():
    """
    List all users for administration.
    ---
    tags:
      - Admin
    responses:
      200:
        description: User list.
        schema:
          type: array
          items:
            $ref: '#/definitions/User'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Admin role required.
        schema:
          $ref: '#/definitions/Error'
    """
    users = get_controllers().admin.list_users()
    return jsonify([serialize_user(user) for user in users])


@api_bp.post("/admin/users")
@login_required
@roles_required(Role.ADMIN)
def create_admin_user_api():
    """
    Create a user account with role assignment.
    ---
    tags:
      - Admin
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          $ref: '#/definitions/AdminUserRequest'
    responses:
      201:
        description: User created.
        schema:
          $ref: '#/definitions/User'
      400:
        description: Validation error.
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Admin role required.
        schema:
          $ref: '#/definitions/Error'
    """
    user = get_controllers().admin.create_user(_payload())
    return jsonify(serialize_user(user)), 201


@api_bp.put("/admin/users/<int:user_id>")
@login_required
@roles_required(Role.ADMIN)
def update_admin_user_api(user_id: int):
    """
    Update a user account and role.
    ---
    tags:
      - Admin
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          $ref: '#/definitions/AdminUserRequest'
    responses:
      200:
        description: User updated.
        schema:
          $ref: '#/definitions/User'
      400:
        description: Validation error.
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Admin role required.
        schema:
          $ref: '#/definitions/Error'
      404:
        description: User not found.
        schema:
          $ref: '#/definitions/Error'
    """
    payload = _payload()
    for bool_field in ["is_active", "email_notifications_enabled"]:
        if bool_field in payload:
            payload[bool_field] = _as_bool(payload.get(bool_field))
    user = get_controllers().admin.update_user(user_id, payload)
    return jsonify(serialize_user(user))


@api_bp.get("/admin/categories")
@login_required
@roles_required(Role.ADMIN)
def admin_categories_api():
    """
    List all categories, including inactive ones.
    ---
    tags:
      - Admin
    responses:
      200:
        description: Category list.
        schema:
          type: array
          items:
            $ref: '#/definitions/Category'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Admin role required.
        schema:
          $ref: '#/definitions/Error'
    """
    categories = get_controllers().admin.list_categories(active_only=False)
    return jsonify([serialize_category(category) for category in categories])


@api_bp.post("/admin/categories")
@login_required
@roles_required(Role.ADMIN)
def create_category_api():
    """
    Create a new report category.
    ---
    tags:
      - Admin
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          $ref: '#/definitions/CategoryRequest'
    responses:
      201:
        description: Category created.
        schema:
          $ref: '#/definitions/Category'
      400:
        description: Validation error.
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Admin role required.
        schema:
          $ref: '#/definitions/Error'
    """
    category = get_controllers().admin.create_category(_payload().get("name", ""))
    return jsonify(serialize_category(category)), 201


@api_bp.put("/admin/categories/<int:category_id>")
@login_required
@roles_required(Role.ADMIN)
def update_category_api(category_id: int):
    """
    Update or deactivate a report category.
    ---
    tags:
      - Admin
    parameters:
      - in: path
        name: category_id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          $ref: '#/definitions/CategoryRequest'
    responses:
      200:
        description: Category updated.
        schema:
          $ref: '#/definitions/Category'
      400:
        description: Validation error.
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Admin role required.
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Category not found.
        schema:
          $ref: '#/definitions/Error'
    """
    payload = _payload()
    if "is_active" in payload:
        payload["is_active"] = _as_bool(payload.get("is_active"))
    category = get_controllers().admin.update_category(category_id, payload)
    return jsonify(serialize_category(category))


@api_bp.get("/admin/stats")
@login_required
@roles_required(Role.ADMIN)
def admin_stats_api():
    """
    Retrieve administrator-only statistics.
    ---
    tags:
      - Admin
    responses:
      200:
        description: Administrative statistics.
        schema:
          $ref: '#/definitions/Statistics'
      401:
        description: Authentication required.
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Admin role required.
        schema:
          $ref: '#/definitions/Error'
    """
    return jsonify(get_controllers().admin.admin_statistics())


