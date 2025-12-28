"""
Unit tests for get_handler, download_handler, and delete_handler.
"""

import pytest
import json
from unittest.mock import Mock, patch
from src.handlers.get_handler import lambda_handler as get_lambda_handler
from src.handlers.download_handler import lambda_handler as download_lambda_handler
from src.handlers.delete_handler import lambda_handler as delete_lambda_handler


class TestGetHandler:
    """Tests for get_handler lambda function."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock Lambda context."""
        context = Mock()
        context.function_name = 'get-handler'
        return context
    
    @patch('src.handlers.get_handler.ImageService')
    def test_successful_get(self, mock_service_class, mock_context):
        """Test successful retrieval of image metadata."""
        event = {
            'pathParameters': {'image_id': '550e8400-e29b-41d4-a716-446655440000'},
            'headers': {'user-id': 'test-user-123'}
        }
        
        mock_service = Mock()
        mock_metadata = Mock()
        mock_metadata.image_id = '550e8400-e29b-41d4-a716-446655440000'
        mock_metadata.filename = 'test.jpg'
        mock_metadata.user_id = 'test-user-123'
        mock_service.get_image_metadata.return_value = (True, mock_metadata, None)
        mock_service_class.return_value = mock_service
        
        response = get_lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 200
    
    def test_missing_image_id(self, mock_context):
        """Test error when image_id is missing."""
        event = {
            'pathParameters': {},
            'headers': {'user-id': 'test-user-123'}
        }

        response = get_lambda_handler(event, mock_context)

        assert response['statusCode'] == 422    def test_invalid_image_id(self, mock_context):
        """Test error with invalid image_id format."""
        event = {
            'pathParameters': {'image_id': 'not-a-uuid'},
            'headers': {'user-id': 'test-user-123'}
        }

        response = get_lambda_handler(event, mock_context)

        assert response['statusCode'] == 422
    
    @patch('src.handlers.get_handler.ImageService')
    def test_image_not_found(self, mock_service_class, mock_context):
        """Test 404 when image doesn't exist."""
        event = {
            'pathParameters': {'image_id': '550e8400-e29b-41d4-a716-446655440000'},
            'headers': {'user-id': 'test-user-123'}
        }
        
        mock_service = Mock()
        mock_service.get_image_metadata.return_value = (False, None, 'Image not found')
        mock_service_class.return_value = mock_service
        
        response = get_lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 404
    
    @patch('src.handlers.get_handler.ImageService')
    def test_unauthorized_access(self, mock_service_class, mock_context):
        """Test 403 for unauthorized access."""
        event = {
            'pathParameters': {'image_id': '550e8400-e29b-41d4-a716-446655440000'},
            'headers': {'user-id': 'test-user-123'}
        }
        
        mock_service = Mock()
        mock_service.get_image_metadata.return_value = (False, None, 'Unauthorized access')
        mock_service_class.return_value = mock_service
        
        response = get_lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 403


class TestDownloadHandler:
    """Tests for download_handler lambda function."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock Lambda context."""
        context = Mock()
        context.function_name = 'download-handler'
        return context
    
    @patch('src.handlers.download_handler.ImageService')
    def test_successful_download_url(self, mock_service_class, mock_context):
        """Test successful generation of download URL."""
        event = {
            'pathParameters': {'image_id': '550e8400-e29b-41d4-a716-446655440000'},
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {}
        }
        
        mock_service = Mock()
        mock_service.generate_presigned_url.return_value = (
            True,
            'https://s3.amazonaws.com/bucket/key?signature=xyz',
            None
        )
        mock_service_class.return_value = mock_service
        
        response = download_lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'presigned_url' in body['data']
    
    @patch('src.handlers.download_handler.ImageService')
    def test_redirect_mode(self, mock_service_class, mock_context):
        """Test redirect mode (302 response)."""
        event = {
            'pathParameters': {'image_id': '550e8400-e29b-41d4-a716-446655440000'},
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {'redirect': 'true'}
        }
        
        mock_service = Mock()
        mock_service.generate_presigned_url.return_value = (
            True,
            'https://s3.amazonaws.com/bucket/key',
            None
        )
        mock_service_class.return_value = mock_service
        
        response = download_lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 302
        assert 'Location' in response['headers']
    
    @patch('src.handlers.download_handler.ImageService')
    def test_custom_expiry(self, mock_service_class, mock_context):
        """Test custom expiry time."""
        event = {
            'pathParameters': {'image_id': '550e8400-e29b-41d4-a716-446655440000'},
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {'expiry': '1800'}
        }
        
        mock_service = Mock()
        mock_service.generate_presigned_url.return_value = (True, 'https://s3.url', None)
        mock_service_class.return_value = mock_service
        
        response = download_lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 200
        # Verify expiry was passed
        call_kwargs = mock_service.generate_presigned_url.call_args[1]
        assert call_kwargs['expiry'] == 1800
    
    def test_invalid_expiry(self, mock_context):
        """Test error with invalid expiry."""
        event = {
            'pathParameters': {'image_id': '550e8400-e29b-41d4-a716-446655440000'},
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {'expiry': 'invalid'}
        }

        response = download_lambda_handler(event, mock_context)

        assert response['statusCode'] == 422    @patch('src.handlers.download_handler.ImageService')
    def test_image_not_found(self, mock_service_class, mock_context):
        """Test 404 when image doesn't exist."""
        event = {
            'pathParameters': {'image_id': '550e8400-e29b-41d4-a716-446655440000'},
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {}
        }
        
        mock_service = Mock()
        mock_service.generate_presigned_url.return_value = (False, None, 'Image not found')
        mock_service_class.return_value = mock_service
        
        response = download_lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 404


class TestDeleteHandler:
    """Tests for delete_handler lambda function."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock Lambda context."""
        context = Mock()
        context.function_name = 'delete-handler'
        return context
    
    @patch('src.handlers.delete_handler.ImageService')
    def test_successful_soft_delete(self, mock_service_class, mock_context):
        """Test successful soft delete."""
        event = {
            'pathParameters': {'image_id': '550e8400-e29b-41d4-a716-446655440000'},
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {}
        }
        
        mock_service = Mock()
        mock_service.delete_image.return_value = (True, None)
        mock_service_class.return_value = mock_service
        
        response = delete_lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 200
        # Verify soft_delete was True
        call_kwargs = mock_service.delete_image.call_args[1]
        assert call_kwargs['soft_delete'] is True
    
    @patch('src.handlers.delete_handler.ImageService')
    def test_successful_hard_delete(self, mock_service_class, mock_context):
        """Test successful hard delete."""
        event = {
            'pathParameters': {'image_id': '550e8400-e29b-41d4-a716-446655440000'},
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {'hard_delete': 'true'}
        }
        
        mock_service = Mock()
        mock_service.delete_image.return_value = (True, None)
        mock_service_class.return_value = mock_service
        
        response = delete_lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 200
        # Verify soft_delete was False
        call_kwargs = mock_service.delete_image.call_args[1]
        assert call_kwargs['soft_delete'] is False
    
    def test_missing_image_id(self, mock_context):
        """Test error when image_id is missing."""
    def test_missing_image_id(self, mock_context):
        """Test error when image_id is missing."""
        event = {
            'pathParameters': {},
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {}
        }

        response = delete_lambda_handler(event, mock_context)

        assert response['statusCode'] == 422        """Test 404 when image doesn't exist."""
        event = {
            'pathParameters': {'image_id': '550e8400-e29b-41d4-a716-446655440000'},
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {}
        }
        
        mock_service = Mock()
        mock_service.delete_image.return_value = (False, 'Image not found')
        mock_service_class.return_value = mock_service
        
        response = delete_lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 404
    
    @patch('src.handlers.delete_handler.ImageService')
    def test_unauthorized_access(self, mock_service_class, mock_context):
        """Test 403 for unauthorized access."""
        event = {
            'pathParameters': {'image_id': '550e8400-e29b-41d4-a716-446655440000'},
            'headers': {'user-id': 'test-user-123'},
            'queryStringParameters': {}
        }
        
        mock_service = Mock()
        mock_service.delete_image.return_value = (False, 'Unauthorized access')
        mock_service_class.return_value = mock_service
        
        response = delete_lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 403
