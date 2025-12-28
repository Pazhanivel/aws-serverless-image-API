"""
Unit tests for list_handler.
"""

import pytest
import json
from unittest.mock import Mock, patch
from src.handlers.list_handler import lambda_handler, parse_query_parameters


class TestParseQueryParameters:
    """Tests for parse_query_parameters function."""
    
    def test_parse_basic_params(self):
        """Test parsing basic query parameters."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {
                'limit': '10',
                'status': 'active'
            }
        }
        
        params = parse_query_parameters(event)
        
        assert params['user_id'] == 'test-user-123'
        assert params['limit'] == 10
        assert params['status'] == 'active'
    
    def test_parse_tags(self):
        """Test parsing comma-separated tags."""
        event = {
            'headers': {'user-id': 'test-user'},
            'queryStringParameters': {
                'tags': 'vacation,beach,sunset'
            }
        }
        
        params = parse_query_parameters(event)
        
        assert params['tags'] == ['vacation', 'beach', 'sunset']
    
    def test_parse_tags_with_spaces(self):
        """Test parsing tags with spaces."""
        event = {
            'headers': {'user-id': 'test-user'},
            'queryStringParameters': {
                'tags': ' vacation , beach , sunset '
            }
        }
        
        params = parse_query_parameters(event)
        
        assert params['tags'] == ['vacation', 'beach', 'sunset']
    
    def test_parse_size_filters(self):
        """Test parsing size filters."""
        event = {
            'headers': {'user-id': 'test-user'},
            'queryStringParameters': {
                'min_size': '1024',
                'max_size': '5242880'
            }
        }
        
        params = parse_query_parameters(event)
        
        assert params['min_size'] == 1024
        assert params['max_size'] == 5242880
    
    def test_limit_cap(self):
        """Test that limit is capped at 100."""
        event = {
            'headers': {'user-id': 'test-user'},
            'queryStringParameters': {
                'limit': '500'
            }
        }
        
        params = parse_query_parameters(event)
        
        assert params['limit'] == 100
    
    def test_default_values(self):
        """Test default values."""
        event = {
            'headers': {'user-id': 'test-user'},
            'queryStringParameters': {}
        }
        
        params = parse_query_parameters(event)
        
        assert params['limit'] == 50
        assert params['status'] is None  # No default status filter
        assert params['tags'] is None
    
    def test_invalid_limit(self):
        """Test handling of invalid limit."""
        event = {
            'headers': {'user-id': 'test-user'},
            'queryStringParameters': {
                'limit': 'invalid'
            }
        }
        
        params = parse_query_parameters(event)
        
        assert params['limit'] == 50  # Falls back to default


class TestListHandler:
    """Tests for list_handler lambda function."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock Lambda context."""
        context = Mock()
        context.function_name = 'list-handler'
        context.request_id = 'test-request-id'
        return context
    
    @patch('src.handlers.list_handler.ImageService')
    def test_successful_list(self, mock_service_class, mock_context):
        """Test successful image listing."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {}
        }
        
        # Setup mock
        mock_service = Mock()
        mock_metadata1 = Mock()
        mock_metadata1.image_id = 'img1'
        mock_metadata1.user_id = 'test-user-123'
        mock_metadata1.filename = 'test1.jpg'
        mock_metadata1.content_type = 'image/jpeg'
        mock_metadata1.size = 1024
        mock_metadata1.upload_timestamp = '2025-12-28T00:00:00Z'
        mock_metadata1.tags = []
        mock_metadata1.description = None
        mock_metadata1.width = None
        mock_metadata1.height = None
        mock_metadata1.status = 'active'
        
        mock_metadata2 = Mock()
        mock_metadata2.image_id = 'img2'
        mock_metadata2.user_id = 'test-user-123'
        mock_metadata2.filename = 'test2.jpg'
        mock_metadata2.content_type = 'image/jpeg'
        mock_metadata2.size = 2048
        mock_metadata2.upload_timestamp = '2025-12-28T00:00:01Z'
        mock_metadata2.tags = []
        mock_metadata2.description = None
        mock_metadata2.width = None
        mock_metadata2.height = None
        mock_metadata2.status = 'active'
        
        mock_service.list_user_images.return_value = (
            True,
            [mock_metadata1, mock_metadata2],
            None,
            None
        )
        mock_service_class.return_value = mock_service
        
        response = lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'data' in body
        assert 'items' in body['data']
        assert len(body['data']['items']) == 2
    
    def test_missing_user_id(self, mock_context):
        """Test error when user-id is missing."""
        event = {
            'headers': {},
            'queryStringParameters': {}
        }

        response = lambda_handler(event, mock_context)

        assert response['statusCode'] == 422
        body = json.loads(response['body'])
        assert body['success'] is False
    
    @patch('src.handlers.list_handler.ImageService')
    def test_with_pagination(self, mock_service_class, mock_context):
        """Test listing with pagination."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {
                'limit': '2'
            }
        }
        
        mock_service = Mock()
        mock_metadata = Mock()
        mock_metadata.image_id = 'img1'
        mock_metadata.user_id = 'test-user-123'
        mock_metadata.filename = 'test.jpg'
        mock_metadata.content_type = 'image/jpeg'
        mock_metadata.size = 1024
        mock_metadata.upload_timestamp = '2025-12-28T00:00:00Z'
        mock_metadata.tags = []
        mock_metadata.description = None
        mock_metadata.width = None
        mock_metadata.height = None
        mock_metadata.status = 'active'
        
        next_key = {'image_id': 'last-id'}
        mock_service.list_user_images.return_value = (
            True,
            [mock_metadata],
            next_key,
            None
        )
        mock_service_class.return_value = mock_service
        
        response = lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'data' in body
        assert len(body['data']['items']) <= 2
    
    @patch('src.handlers.list_handler.ImageService')
    def test_with_tag_filter(self, mock_service_class, mock_context):
        """Test listing with tag filter."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {
                'tags': 'vacation,beach'
            }
        }
        
        mock_service = Mock()
        mock_service.search_images.return_value = (True, [], None, None)
        mock_service_class.return_value = mock_service
        
        response = lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 200
        # Verify search_images was called with tags
        mock_service.search_images.assert_called_once()
        call_kwargs = mock_service.search_images.call_args[1]
        assert 'tags' in call_kwargs
    
    @patch('src.handlers.list_handler.ImageService')
    def test_with_content_type_filter(self, mock_service_class, mock_context):
        """Test listing with content_type filter."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {
                'content_type': 'image/png'
            }
        }
        
        mock_service = Mock()
        mock_service.search_images.return_value = (True, [], None, None)
        mock_service_class.return_value = mock_service
        
        response = lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 200
        call_kwargs = mock_service.search_images.call_args[1]
        assert call_kwargs['content_type'] == 'image/png'
    
    @patch('src.handlers.list_handler.ImageService')
    def test_with_size_filters(self, mock_service_class, mock_context):
        """Test listing with size filters."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {
                'min_size': '1024',
                'max_size': '5242880'
            }
        }
        
        mock_service = Mock()
        mock_service.search_images.return_value = (True, [], None, None)
        mock_service_class.return_value = mock_service
        
        response = lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 200
        call_kwargs = mock_service.search_images.call_args[1]
        assert call_kwargs['min_size'] == 1024
        assert call_kwargs['max_size'] == 5242880
    
    @patch('src.handlers.list_handler.ImageService')
    def test_empty_result(self, mock_service_class, mock_context):
        """Test listing with no results."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {}
        }
        
        mock_service = Mock()
        mock_service.list_user_images.return_value = (True, [], None, None)
        mock_service_class.return_value = mock_service
        
        response = lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['data']['items'] == []
    
    @patch('src.handlers.list_handler.ImageService')
    def test_service_error(self, mock_service_class, mock_context):
        """Test handling of service error."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {}
        }
        
        mock_service = Mock()
        mock_service.list_user_images.return_value = (
            False,
            [],
            None,
            'Service error occurred'
        )
        mock_service_class.return_value = mock_service
        
        response = lambda_handler(event, mock_context)

        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'message' in body