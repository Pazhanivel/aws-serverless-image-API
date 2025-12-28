"""
Input validation utilities for the image service.
Provides validation functions for image metadata and user input.
Note: Since we use presigned URLs, files never go through Lambda, so no PIL/image validation needed.
"""

import re
from typing import List, Optional, Tuple


def validate_content_type(content_type: str, allowed_types: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate image content type.
    
    Args:
        content_type: MIME type to validate
        allowed_types: List of allowed MIME types (if None, uses defaults)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if allowed_types is None:
        from src.config.settings import settings
        allowed_types = settings.ALLOWED_CONTENT_TYPES
    
    if not content_type:
        return False, "Content type is required"
    
    if content_type.lower() not in [ct.lower() for ct in allowed_types]:
        return False, f"Content type '{content_type}' is not allowed. Allowed types: {', '.join(allowed_types)}"
    
    return True, None


def validate_file_size(size: int, max_size: Optional[int] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate file size.
    
    Args:
        size: File size in bytes
        max_size: Maximum allowed size in bytes (if None, uses default from settings)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if max_size is None:
        from src.config.settings import settings
        max_size = settings.MAX_IMAGE_SIZE
    
    if size <= 0:
        return False, "File size must be greater than 0"
    
    if size > max_size:
        max_mb = max_size / (1024 * 1024)
        current_mb = size / (1024 * 1024)
        return False, f"File size ({current_mb:.2f} MB) exceeds maximum allowed size ({max_mb:.2f} MB)"
    
    return True, None


def validate_user_id(user_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate user ID format.
    
    Args:
        user_id: User identifier
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not user_id:
        return False, "User ID is required"
    
    if not isinstance(user_id, str):
        return False, "User ID must be a string"
    
    if len(user_id) < 3 or len(user_id) > 128:
        return False, "User ID must be between 3 and 128 characters"
    
    # Allow alphanumeric, hyphens, and underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
        return False, "User ID can only contain letters, numbers, hyphens, and underscores"
    
    return True, None


def validate_tags(tags: List[str], max_tags: int = 10, max_tag_length: int = 50) -> Tuple[bool, Optional[str]]:
    """
    Validate tags list.
    
    Args:
        tags: List of tag strings
        max_tags: Maximum number of tags allowed
        max_tag_length: Maximum length of each tag
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(tags, list):
        return False, "Tags must be a list"
    
    if len(tags) > max_tags:
        return False, f"Maximum {max_tags} tags allowed"
    
    for tag in tags:
        if not isinstance(tag, str):
            return False, "Each tag must be a string"
        
        if not tag.strip():
            return False, "Tags cannot be empty"
        
        if len(tag) > max_tag_length:
            return False, f"Tag '{tag[:20]}...' exceeds maximum length of {max_tag_length} characters"
        
        # Allow alphanumeric, spaces, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9 _-]+$', tag):
            return False, f"Tag '{tag}' contains invalid characters"
    
    return True, None


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename to remove dangerous characters.
    
    Args:
        filename: Original filename
        max_length: Maximum length for filename
    
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"
    
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Replace dangerous characters with underscores
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        if ext:
            max_name_length = max_length - len(ext) - 1
            filename = name[:max_name_length] + '.' + ext
        else:
            filename = filename[:max_length]
    
    return filename or "unnamed"


def validate_description(description: Optional[str], max_length: int = 500) -> Tuple[bool, Optional[str]]:
    """
    Validate description text.
    
    Args:
        description: Description text
        max_length: Maximum length allowed
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if description is None:
        return True, None  # Description is optional
    
    if not isinstance(description, str):
        return False, "Description must be a string"
    
    if len(description) > max_length:
        return False, f"Description exceeds maximum length of {max_length} characters"
    
    return True, None


def validate_image_id(image_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate image ID format (UUID).
    
    Args:
        image_id: Image identifier
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not image_id:
        return False, "Image ID is required"
    
    # UUID format validation
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(uuid_pattern, image_id.lower()):
        return False, "Invalid image ID format"
    
    return True, None
