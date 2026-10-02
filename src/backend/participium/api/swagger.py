from __future__ import annotations

from flasgger import Swagger


def _array_of(definition_name: str) -> dict:
    return {
        "type": "array",
        "items": {"$ref": f"#/definitions/{definition_name}"},
    }


def _message_response(message: str) -> dict:
    return {
        "type": "object",
        "required": ["message"],
        "properties": {
            "message": {"type": "string", "example": message},
        },
    }


def init_swagger(app):
    template = {
        "swagger": "2.0",
        "info": {
            "title": "Participium API",
            "description": "REST API for the Participium civic issue reporting platform.",
            "version": "1.0.0",
        },
        "basePath": "/api/v1",
        "schemes": ["http", "https"],
        "consumes": ["application/json", "multipart/form-data"],
        "produces": ["application/json"],
        "definitions": _definitions(),
    }
    Swagger(app, template=template)


def _definitions() -> dict:
    role_enum = ["citizen", "operator", "admin"]
    report_status_enum = [
        "Pending Approval",
        "Assigned",
        "In Progress",
        "Suspended",
        "Rejected",
        "Resolved",
    ]

    return {
        "Error": {
            "type": "object",
            "required": ["error"],
            "properties": {"error": {"type": "string"}},
        },
        "Health": {
            "type": "object",
            "required": ["status"],
            "properties": {"status": {"type": "string", "example": "ok"}},
        },
        "ReferenceData": {
            "type": "object",
            "required": ["roles", "report_statuses", "public_report_statuses"],
            "properties": {
                "roles": {"type": "array", "items": {"type": "string", "enum": role_enum}},
                "report_statuses": {
                    "type": "array",
                    "items": {"type": "string", "enum": report_status_enum},
                },
                "public_report_statuses": {
                    "type": "array",
                    "items": {"type": "string", "enum": report_status_enum},
                },
            },
        },
        "Category": {
            "type": "object",
            "required": ["id", "name", "is_active"],
            "properties": {
                "id": {"type": "integer", "example": 1},
                "name": {"type": "string", "example": "Roads and Urban Furniture"},
                "is_active": {"type": "boolean"},
                "created_at": {"type": "string", "format": "date-time", "x-nullable": True},
            },
        },
        "Party": {
            "type": "object",
            "required": ["id", "display_name", "role"],
            "properties": {
                "id": {"type": "integer", "x-nullable": True},
                "display_name": {"type": "string", "example": "Marco Citizen"},
                "role": {"type": "string", "enum": role_enum, "x-nullable": True},
            },
        },
        "User": {
            "type": "object",
            "required": [
                "id",
                "username",
                "first_name",
                "last_name",
                "email",
                "role",
                "is_active",
                "is_email_verified",
                "email_notifications_enabled",
            ],
            "properties": {
                "id": {"type": "integer", "example": 1},
                "username": {"type": "string", "example": "citizen"},
                "first_name": {"type": "string", "example": "Marco"},
                "last_name": {"type": "string", "example": "Citizen"},
                "email": {"type": "string", "format": "email", "example": "citizen@example.com"},
                "role": {"type": "string", "enum": role_enum},
                "category_id": {"type": "integer", "x-nullable": True},
                "category": {"$ref": "#/definitions/Category"},
                "is_active": {"type": "boolean"},
                "is_email_verified": {"type": "boolean"},
                "email_notifications_enabled": {"type": "boolean"},
                "profile_picture_path": {"type": "string", "x-nullable": True},
                "profile_picture_url": {"type": "string", "x-nullable": True},
                "created_at": {"type": "string", "format": "date-time", "x-nullable": True},
            },
        },
        "Photo": {
            "type": "object",
            "required": ["id", "file_path", "url", "original_filename", "content_type"],
            "properties": {
                "id": {"type": "integer"},
                "file_path": {"type": "string"},
                "url": {"type": "string", "x-nullable": True},
                "original_filename": {"type": "string"},
                "content_type": {"type": "string", "example": "image/jpeg"},
            },
        },
        "ReportSummary": {
            "type": "object",
            "required": [
                "id",
                "title",
                "description",
                "category",
                "status",
                "is_anonymous",
                "reporter",
                "latitude",
                "longitude",
                "photos",
                "followers_count",
                "is_followed_by_current_user",
                "is_public",
            ],
            "properties": {
                "id": {"type": "integer", "example": 10},
                "title": {"type": "string", "example": "Pothole on Via Roma"},
                "description": {"type": "string"},
                "category": {"$ref": "#/definitions/Category"},
                "status": {"type": "string", "enum": report_status_enum},
                "rejection_reason": {"type": "string", "x-nullable": True},
                "is_anonymous": {"type": "boolean"},
                "reporter": {"$ref": "#/definitions/Party"},
                "latitude": {"type": "number", "format": "float", "example": 45.0678},
                "longitude": {"type": "number", "format": "float", "example": 7.6825},
                "photos": _array_of("Photo"),
                "followers_count": {"type": "integer"},
                "is_followed_by_current_user": {"type": "boolean"},
                "is_public": {"type": "boolean"},
                "created_at": {"type": "string", "format": "date-time", "x-nullable": True},
                "updated_at": {"type": "string", "format": "date-time", "x-nullable": True},
            },
        },
        "StatusHistory": {
            "type": "object",
            "required": ["id", "previous_status", "new_status", "changed_by"],
            "properties": {
                "id": {"type": "integer"},
                "previous_status": {"type": "string", "enum": report_status_enum, "x-nullable": True},
                "new_status": {"type": "string", "enum": report_status_enum},
                "note": {"type": "string", "x-nullable": True},
                "changed_by": {"$ref": "#/definitions/Party"},
                "created_at": {"type": "string", "format": "date-time", "x-nullable": True},
            },
        },
        "ReportDetail": {
            "allOf": [
                {"$ref": "#/definitions/ReportSummary"},
                {
                    "type": "object",
                    "required": ["can_access_messages", "status_history"],
                    "properties": {
                        "can_access_messages": {"type": "boolean"},
                        "status_history": _array_of("StatusHistory"),
                        "messages": _array_of("Message"),
                    },
                },
            ]
        },
        "Message": {
            "type": "object",
            "required": ["id", "report_id", "body", "sender", "recipient"],
            "properties": {
                "id": {"type": "integer"},
                "report_id": {"type": "integer"},
                "body": {"type": "string"},
                "sender": {"$ref": "#/definitions/Party"},
                "recipient": {"$ref": "#/definitions/Party"},
                "created_at": {"type": "string", "format": "date-time", "x-nullable": True},
            },
        },
        "Notification": {
            "type": "object",
            "required": ["id", "type", "title", "body", "is_read"],
            "properties": {
                "id": {"type": "integer"},
                "type": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"},
                "report_id": {"type": "integer", "x-nullable": True},
                "is_read": {"type": "boolean"},
                "created_at": {"type": "string", "format": "date-time", "x-nullable": True},
            },
        },
        "AuthRegisterRequest": {
            "type": "object",
            "required": ["username", "first_name", "last_name", "email", "password"],
            "properties": {
                "username": {"type": "string"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "password": {"type": "string", "format": "password"},
            },
        },
        "AuthRegisterResponse": {
            "type": "object",
            "required": ["user"],
            "properties": {
                "user": {"$ref": "#/definitions/User"},
                "verification_url": {"type": "string"},
            },
        },
        "AuthLoginRequest": {
            "type": "object",
            "required": ["identifier", "password"],
            "properties": {
                "identifier": {"type": "string", "example": "citizen@example.com"},
                "password": {"type": "string", "format": "password"},
            },
        },
        "AuthUserMessageResponse": {
            "type": "object",
            "required": ["message", "user"],
            "properties": {
                "message": {"type": "string"},
                "user": {"$ref": "#/definitions/User"},
            },
        },
        "MessageOnlyResponse": _message_response("Operation completed."),
        "SendMessageRequest": {
            "type": "object",
            "required": ["body"],
            "properties": {"body": {"type": "string"}},
        },
        "UpdateStatusRequest": {
            "type": "object",
            "required": ["status"],
            "properties": {
                "status": {"type": "string", "enum": report_status_enum},
                "note": {"type": "string"},
            },
        },
        "AdminUserRequest": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "password": {"type": "string", "format": "password"},
                "role": {"type": "string", "enum": role_enum},
                "category_id": {"type": "integer"},
                "is_active": {"type": "boolean"},
                "email_notifications_enabled": {"type": "boolean"},
            },
        },
        "CategoryRequest": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "is_active": {"type": "boolean"},
            },
        },
        "Statistics": {
            "type": "object",
            "additionalProperties": True,
        },
    }
