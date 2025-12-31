"""
Configuration settings for the timetable generator.
Centralized configuration management for better maintainability.
"""

import os
from typing import Dict, Any

# Security Settings
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_MATT_PASSWORD = "remy11"
DEFAULT_LECTURER_PASSWORD = "mathy11"

# Database Configuration
DATABASE_NAME = "timetable.db"
USERS_DATABASE_NAME = "users.db"
CONNECTION_POOL_SIZE = 20
DATABASE_TIMEOUT = 30

# Session Management
SESSION_TIMEOUT_HOURS = 1
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 5

# Email Configuration 
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "matthewkasango@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "wfxg alzt djek mjgp")

# UI Configuration
DEFAULT_ROOM_CAPACITY = 500
DEFAULT_NUM_ROOMS = 5
DEFAULT_STUDENT_COUNT = 30

# Validation Messages
VALIDATION_MESSAGES = {
    "program_required": "Please enter a program code",
    "program_exists": "Program '{}' already exists!",
    "level_required": "Please enter a level",
    "level_exists": "Level '{}' already exists!",
    "department_exists": "Department already exists!",
    "room_prefix_required": "Please enter a room prefix",
    "password_mismatch": "Passwords do not match!",
    "password_too_short": "Password must be at least 6 characters long!",
    "email_required": "Please enter a valid email address!",
    "username_exists": "Username already exists!",
    "email_exists": "Email already registered!"
}

# Error Messages
ERROR_MESSAGES = {
    "authentication_failed": "Invalid username or password.",
    "access_denied": "You do not have permission to access this feature.",
    "session_expired": "Session expired. Please login again.",
    "database_error": "Database operation failed. Please try again.",
    "validation_error": "Input validation failed. Please check your entries."
}

# Success Messages
SUCCESS_MESSAGES = {
    "user_created": "User created successfully!",
    "password_updated": "Password updated successfully!",
    "department_created": "Department created successfully!",
    "timetable_generated": "Timetable generated successfully!",
    "configuration_saved": "Configuration saved successfully!"
}

# Password Strength Configuration
PASSWORD_STRENGTH = {
    "min_length": 6,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digits": True,
    "require_special": False
}

# Algorithm Default Parameters
ALGORITHM_DEFAULTS = {
    "population_size": 200,
    "generations": 1000,
    "mutation_rate": 0.15,
    "tournament_size": 5,
    "elitism_count": 5
}

# File Upload Configuration
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = ['csv', 'xlsx', 'json']

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "timetable.log"
AUDIT_LOG_FILE = "audit.log"

def get_validation_message(key: str, *args) -> str:
    """Get a validation message with optional formatting."""
    message = VALIDATION_MESSAGES.get(key, "Unknown validation error")
    return message.format(*args) if args else message

def get_error_message(key: str) -> str:
    """Get an error message."""
    return ERROR_MESSAGES.get(key, "An unknown error occurred.")

def get_success_message(key: str) -> str:
    """Get a success message."""
    return SUCCESS_MESSAGES.get(key, "Operation completed successfully.")

def is_production() -> bool:
    """Check if running in production environment."""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"

def get_database_url() -> str:
    """Get database connection URL."""
    if is_production():
        return os.getenv("DATABASE_URL", f"sqlite://{DATABASE_NAME}")
    return f"sqlite://{DATABASE_NAME}"
