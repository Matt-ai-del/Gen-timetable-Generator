import re
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

def safe_latin1(text):
    """Convert problematic unicode characters to safe latin1 equivalents"""
    if not text:
        return ""
    return text.replace('–', '-').replace('—', '-')

def validate_email(email: str) -> bool:
    """Validate email format using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_course_code(course_code: str) -> bool:
    """Validate course code format (e.g., 'CS101', 'MATH202')"""
    pattern = r'^[A-Z]{2,4}\d{3,4}$'
    return re.match(pattern, course_code.upper()) is not None

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not text:
        return ""
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '{', '}']
    for char in dangerous_chars:
        text = text.replace(char, '')
    return text.strip()[:500]  # Limit length

def validate_time_slot(time_slot: str) -> bool:
    """Validate time slot format"""
    valid_slots = ["08:00-10:00", "10:00-12:00", "12:00-14:00", "14:00-16:00"]
    return time_slot in valid_slots

def validate_day(day: str) -> bool:
    """Validate day format"""
    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    return day in valid_days

def safe_int_convert(value: Any, default: int = 0) -> int:
    """Safely convert value to integer with fallback"""
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert {value} to int, using default {default}")
        return default

def safe_float_convert(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float with fallback"""
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert {value} to float, using default {default}")
        return default

def validate_faculty_workload(hours: int) -> bool:
    """Validate faculty workload is within acceptable range"""
    return 4 <= hours <= 40

def log_error(error: Exception, context: str = "") -> None:
    """Enhanced error logging with context"""
    error_msg = f"{context}: {str(error)}" if context else str(error)
    logger.error(error_msg, exc_info=True)

def validate_json_structure(data: Dict[str, Any], required_keys: List[str]) -> bool:
    """Validate JSON structure contains required keys"""
    if not isinstance(data, dict):
        return False
    return all(key in data for key in required_keys)

def safe_filename(filename: str) -> str:
    """Generate safe filename by removing dangerous characters"""
    if not filename:
        return f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    # Remove path traversal and dangerous characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    safe_name = re.sub(r'\.\.', '_', safe_name)
    return safe_name[:100]  # Limit length