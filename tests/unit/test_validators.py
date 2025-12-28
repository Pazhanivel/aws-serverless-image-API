"""
Unit tests for validators module.
"""

import pytest
from src.utils.validators import (
    validate_content_type,
    validate_file_size,
    validate_user_id,
    validate_tags,
    validate_description,
    sanitize_filename,
    validate_image_id
)


class TestValidateContentType:
    """Tests for validate_content_type function."""
    
    def test_valid_jpeg(self):
        is_valid, error = validate_content_type('image/jpeg')
        assert is_valid is True
        assert error is None
    
    def test_valid_png(self):
        is_valid, error = validate_content_type('image/png')
        assert is_valid is True
        assert error is None
    
    def test_valid_gif(self):
        is_valid, error = validate_content_type('image/gif')
        assert is_valid is True
        assert error is None
    
    def test_valid_webp(self):
        is_valid, error = validate_content_type('image/webp')
        assert is_valid is True
        assert error is None
    
    def test_case_insensitive(self):
        is_valid, error = validate_content_type('Image/JPEG')
        assert is_valid is True
        assert error is None
    
    def test_invalid_content_type(self):
        is_valid, error = validate_content_type('text/plain')
        assert is_valid is False
        assert 'not allowed' in error.lower()
    
    def test_empty_content_type(self):
        is_valid, error = validate_content_type('')
        assert is_valid is False
        assert 'required' in error.lower()
    
    def test_none_content_type(self):
        is_valid, error = validate_content_type(None)
        assert is_valid is False
        assert 'required' in error.lower()
    
    def test_custom_allowed_types(self):
        is_valid, error = validate_content_type('image/tiff', allowed_types=['image/tiff'])
        assert is_valid is True
        assert error is None


class TestValidateFileSize:
    """Tests for validate_file_size function."""
    
    def test_valid_small_file(self):
        is_valid, error = validate_file_size(1024)  # 1 KB
        assert is_valid is True
        assert error is None
    
    def test_valid_medium_file(self):
        is_valid, error = validate_file_size(5 * 1024 * 1024)  # 5 MB
        assert is_valid is True
        assert error is None
    
    def test_valid_max_size(self):
        # Default max is 10MB
        is_valid, error = validate_file_size(10 * 1024 * 1024)
        assert is_valid is True
        assert error is None
    
    def test_file_too_large(self):
        is_valid, error = validate_file_size(15 * 1024 * 1024)  # 15 MB
        assert is_valid is False
        assert 'exceeds' in error.lower()
    
    def test_zero_size(self):
        is_valid, error = validate_file_size(0)
        assert is_valid is False
        assert 'greater than 0' in error.lower()
    
    def test_negative_size(self):
        is_valid, error = validate_file_size(-100)
        assert is_valid is False
        assert 'greater than 0' in error.lower()
    
    def test_custom_max_size(self):
        is_valid, error = validate_file_size(2048, max_size=1024)
        assert is_valid is False
        assert 'exceeds' in error.lower()


class TestValidateUserId:
    """Tests for validate_user_id function."""
    
    def test_valid_user_id(self):
        is_valid, error = validate_user_id('user123')
        assert is_valid is True
        assert error is None
    
    def test_valid_with_hyphens(self):
        is_valid, error = validate_user_id('user-123-abc')
        assert is_valid is True
        assert error is None
    
    def test_valid_with_underscores(self):
        is_valid, error = validate_user_id('user_123_abc')
        assert is_valid is True
        assert error is None
    
    def test_valid_mixed(self):
        is_valid, error = validate_user_id('User_123-ABC')
        assert is_valid is True
        assert error is None
    
    def test_empty_user_id(self):
        is_valid, error = validate_user_id('')
        assert is_valid is False
        assert 'required' in error.lower()
    
    def test_none_user_id(self):
        is_valid, error = validate_user_id(None)
        assert is_valid is False
        assert 'required' in error.lower()
    
    def test_too_short(self):
        is_valid, error = validate_user_id('ab')
        assert is_valid is False
        assert 'between 3 and 128' in error.lower()
    
    def test_too_long(self):
        is_valid, error = validate_user_id('a' * 129)
        assert is_valid is False
        assert 'between 3 and 128' in error.lower()
    
    def test_invalid_characters_space(self):
        is_valid, error = validate_user_id('user 123')
        assert is_valid is False
        assert 'only contain' in error.lower()
    
    def test_invalid_characters_special(self):
        is_valid, error = validate_user_id('user@123')
        assert is_valid is False
        assert 'only contain' in error.lower()
    
    def test_not_string(self):
        is_valid, error = validate_user_id(12345)
        assert is_valid is False
        assert 'must be a string' in error.lower()


class TestValidateTags:
    """Tests for validate_tags function."""
    
    def test_valid_single_tag(self):
        is_valid, error = validate_tags(['vacation'])
        assert is_valid is True
        assert error is None
    
    def test_valid_multiple_tags(self):
        is_valid, error = validate_tags(['vacation', 'beach', 'summer-2024'])
        assert is_valid is True
        assert error is None
    
    def test_valid_with_spaces(self):
        is_valid, error = validate_tags(['my vacation', 'summer trip'])
        assert is_valid is True
        assert error is None
    
    def test_valid_with_underscores(self):
        is_valid, error = validate_tags(['my_vacation', 'beach_day'])
        assert is_valid is True
        assert error is None
    
    def test_empty_list(self):
        is_valid, error = validate_tags([])
        assert is_valid is True
        assert error is None
    
    def test_too_many_tags(self):
        is_valid, error = validate_tags([f'tag{i}' for i in range(11)])  # 11 tags
        assert is_valid is False
        assert 'maximum' in error.lower()
    
    def test_tag_too_long(self):
        is_valid, error = validate_tags(['a' * 51])
        assert is_valid is False
        assert 'exceeds maximum length' in error.lower()
    
    def test_empty_tag(self):
        is_valid, error = validate_tags([''])
        assert is_valid is False
        assert 'cannot be empty' in error.lower()
    
    def test_whitespace_tag(self):
        is_valid, error = validate_tags(['   '])
        assert is_valid is False
        assert 'cannot be empty' in error.lower()
    
    def test_invalid_characters(self):
        is_valid, error = validate_tags(['tag@123'])
        assert is_valid is False
        assert 'invalid characters' in error.lower()
    
    def test_not_list(self):
        is_valid, error = validate_tags('vacation')
        assert is_valid is False
        assert 'must be a list' in error.lower()
    
    def test_non_string_in_list(self):
        is_valid, error = validate_tags(['vacation', 123])
        assert is_valid is False
        assert 'must be a string' in error.lower()


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""
    
    def test_simple_filename(self):
        result = sanitize_filename('photo.jpg')
        assert result == 'photo.jpg'
    
    def test_with_spaces(self):
        result = sanitize_filename('my photo.jpg')
        assert result == 'my photo.jpg'
    
    def test_remove_path_unix(self):
        result = sanitize_filename('/path/to/file.jpg')
        assert result == 'file.jpg'
    
    def test_remove_path_windows(self):
        result = sanitize_filename('C:\\path\\to\\file.jpg')
        assert result == 'file.jpg'
    
    def test_dangerous_characters(self):
        result = sanitize_filename('file<>:"|?*.jpg')
        assert '<' not in result
        assert '>' not in result
        assert ':' not in result
        assert '"' not in result
        assert '|' not in result
        assert '?' not in result
        assert '*' not in result
    
    def test_leading_trailing_spaces(self):
        result = sanitize_filename('  file.jpg  ')
        assert result == 'file.jpg'
    
    def test_leading_trailing_dots(self):
        result = sanitize_filename('..file.jpg..')
        assert not result.startswith('.')
        assert not result.endswith('..')
    
    def test_too_long(self):
        long_name = 'a' * 300 + '.jpg'
        result = sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith('.jpg')
    
    def test_empty_filename(self):
        result = sanitize_filename('')
        assert result == 'unnamed'
    
    def test_none_filename(self):
        result = sanitize_filename(None)
        assert result == 'unnamed'
    
    def test_only_invalid_characters(self):
        result = sanitize_filename('<<<>>>')
        assert result == '______' or result == 'unnamed'


class TestValidateDescription:
    """Tests for validate_description function."""
    
    def test_valid_description(self):
        is_valid, error = validate_description('This is a test description')
        assert is_valid is True
        assert error is None
    
    def test_none_description(self):
        is_valid, error = validate_description(None)
        assert is_valid is True
        assert error is None
    
    def test_empty_description(self):
        is_valid, error = validate_description('')
        assert is_valid is True
        assert error is None
    
    def test_max_length(self):
        is_valid, error = validate_description('a' * 500)
        assert is_valid is True
        assert error is None
    
    def test_too_long(self):
        is_valid, error = validate_description('a' * 501)
        assert is_valid is False
        assert 'exceeds maximum length' in error.lower()
    
    def test_not_string(self):
        is_valid, error = validate_description(12345)
        assert is_valid is False
        assert 'must be a string' in error.lower()
    
    def test_custom_max_length(self):
        is_valid, error = validate_description('a' * 100, max_length=50)
        assert is_valid is False
        assert 'exceeds maximum length' in error.lower()
    
    def test_multiline_description(self):
        is_valid, error = validate_description('Line 1\nLine 2\nLine 3')
        assert is_valid is True
        assert error is None


class TestValidateImageId:
    """Tests for validate_image_id function."""
    
    def test_valid_uuid(self):
        is_valid, error = validate_image_id('550e8400-e29b-41d4-a716-446655440000')
        assert is_valid is True
        assert error is None
    
    def test_valid_uuid_lowercase(self):
        is_valid, error = validate_image_id('550e8400-e29b-41d4-a716-446655440000')
        assert is_valid is True
        assert error is None
    
    def test_valid_uuid_uppercase(self):
        is_valid, error = validate_image_id('550E8400-E29B-41D4-A716-446655440000')
        assert is_valid is True
        assert error is None
    
    def test_invalid_format(self):
        is_valid, error = validate_image_id('not-a-uuid')
        assert is_valid is False
        assert 'invalid' in error.lower()
    
    def test_empty_image_id(self):
        is_valid, error = validate_image_id('')
        assert is_valid is False
        assert 'required' in error.lower()
    
    def test_none_image_id(self):
        is_valid, error = validate_image_id(None)
        assert is_valid is False
        assert 'required' in error.lower()
    
    def test_wrong_length(self):
        is_valid, error = validate_image_id('550e8400-e29b-41d4-a716')
        assert is_valid is False
        assert 'invalid' in error.lower()
    
    def test_missing_hyphens(self):
        is_valid, error = validate_image_id('550e8400e29b41d4a716446655440000')
        assert is_valid is False
        assert 'invalid' in error.lower()
