"""
Unit tests for upload_handler.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.handlers.upload_handler import lambda_handler


class TestUploadHandler:
    """Tests for upload_handler lambda function."""
    
    @pytest.fixture
    def mock_event(self):
        """Create a mock Lambda event."""
        return {
            'headers': {
                'user-id': 'test-user-123',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'filename': 'test-image.jpg',
                'content_type': 'image/jpeg',
                'tags': ['test', 'sample'],
                'description': 'Test image'
            }),
            'isBase64Encoded': False
        }
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock Lambda context."""
        context = Mock()
        context.function_name = 'upload-handler'
        context.request_id = 'test-request-id'
        return context
    
    @patch('src.handlers.upload_handler.DynamoDBService')
    @patch('src.handlers.upload_handler.S3Service')
    def test_successful_upload(self, mock_s3_class, mock_dynamodb_class, mock_event, mock_context):
        """Test successful presigned URL generation."""
        mock_s3 = Mock()
        mock_s3.bucket_name = 'test-bucket'
        mock_s3.generate_presigned_upload_url.return_value = (
            True,
            'https://s3.amazonaws.com/test-bucket/test-key?signature=xyz',
            'images/test-user-123/test-image.jpg',
            None
        )
        mock_s3_class.return_value = mock_s3
        
        mock_dynamodb = Mock()
        mock_dynamodb.save_metadata.return_value = (True, None)
        mock_dynamodb_class.return_value = mock_dynamodb
        
        # Execute
        response = lambda_handler(mock_event, mock_context)
        
        # Assert
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert 'image_id' in body
        assert 'upload_url' in body
        assert body['image_id'] == 'test-image-id'
    
    def test_missing_user_id(self, mock_context):
        """Test error when user-id header is missing."""
        event = {
            'headers': {},
            'body': json.dumps({
                'filename': 'test.jpg',
                'content_type': 'image/jpeg'
            })
        }

        response = lambda_handler(event, mock_context)

        assert response['statusCode'] == 422
        body = json.loads(response['body'])
        assert body['success'] == False
        assert 'json' in str(body).lower()
    
    def test_invalid_user_id(self, mock_context):
        \"\"\"Test error with invalid user-id format.\"\"\"
        event = {
            'headers': {'user-id': 'ab'},  # Too short
            'body': json.dumps({
                'filename': 'test.jpg',
                'content_type': 'image/jpeg'
            })
        }

        response = lambda_handler(event, mock_context)

        assert response['statusCode'] == 422
        body = json.loads(response['body'])
        assert body['success'] == False
        assert 'user' in str(body).lower() or 'id' in str(body).lower()
    
    def test_missing_body(self, mock_context):
        """Test error when body is missing."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'body': ''
        }

        response = lambda_handler(event, mock_context)

        assert response['statusCode'] == 422
        body = json.loads(response['body'])
        assert 'error' in body
    
    def test_invalid_json_body(self, mock_context):
        \"\"\"Test error with invalid JSON body.\"\"\"
        event = {
            'headers': {'user-id': 'test-user-123'},
            'body': 'not valid json'
        }

        response = lambda_handler(event, mock_context)

        assert response['statusCode'] == 422
        body = json.loads(response['body'])
        assert body['success'] == False
        assert 'json' in str(body).lower() or 'invalid' in str(body).lower()
    
    def test_missing_filename(self, mock_context):
        """Test error when filename is missing."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'body': json.dumps({
                'content_type': 'image/jpeg'
            })
        }

        response = lambda_handler(event, mock_context)

        assert response['statusCode'] == 422
        body = json.loads(response['body'])
        assert body['success'] == False
        assert 'tag' in str(body).lower()
    
    def test_missing_content_type(self, mock_context):
        """Test error when content_type is missing."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'body': json.dumps({
                'filename': 'test.jpg'
            })
        }

        response = lambda_handler(event, mock_context)

        assert response['statusCode'] == 422
        body = json.loads(response['body'])
        assert body['success'] == False
        assert 'content' in str(body).lower()
    
    def test_invalid_content_type(self, mock_context):
        """Test error with invalid content type."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'body': json.dumps({
                'filename': 'test.txt',
                'content_type': 'text/plain'
            })
        }

        response = lambda_handler(event, mock_context)

        assert response['statusCode'] == 422
        body = json.loads(response['body'])
        assert 'error' in body
    
    @patch('src.handlers.upload_handler.DynamoDBService')
    @patch('src.handlers.upload_handler.S3Service')
    def test_with_tags(self, mock_s3_class, mock_dynamodb_class, mock_context):
        """Test upload with tags."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'body': json.dumps({
                'filename': 'test.jpg',
                'content_type': 'image/jpeg',
                'tags': ['vacation', 'beach', '2024']
            })
        }
        
        mock_s3 = Mock()
        mock_s3.bucket_name = 'test-bucket'
        mock_s3.generate_presigned_upload_url.return_value = (True, 'https://s3.url', 'images/key', None)
        mock_s3_class.return_value = mock_s3
        
        mock_dynamodb = Mock()
        mock_dynamodb.save_metadata.return_value = (True, None)
        mock_dynamodb_class.return_value = mock_dynamodb
        
        response = lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['success'] == True
    
    @patch('src.handlers.upload_handler.DynamoDBService')
    @patch('src.handlers.upload_handler.S3Service')
    def test_with_description(self, mock_s3_class, mock_dynamodb_class, mock_context):
        """Test upload with description."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'body': json.dumps({
                'filename': 'test.jpg',
                'content_type': 'image/jpeg',
                'description': 'A beautiful sunset'
            })
        }
        
        mock_s3 = Mock()
        mock_s3.bucket_name = 'test-bucket'
        mock_s3.generate_presigned_upload_url.return_value = (True, 'https://s3.url', 'images/key', None)
        mock_s3_class.return_value = mock_s3
        
        mock_dynamodb = Mock()
        mock_dynamodb.save_metadata.return_value = (True, None)
        mock_dynamodb_class.return_value = mock_dynamodb
        
        response = lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 200
    
    def test_invalid_tags(self, mock_context):
        """Test error with invalid tags."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'body': json.dumps({
                'filename': 'test.jpg',
                'content_type': 'image/jpeg',
                'tags': 'not-a-list'
            })
        }

        response = lambda_handler(event, mock_context)

        assert response['statusCode'] == 422
        body = json.loads(response['body'])
        assert 'error' in body
    
    @patch('src.handlers.upload_handler.DynamoDBService')
    @patch('src.handlers.upload_handler.S3Service')
    @patch('src.handlers.upload_handler.ImageMetadata')
    def test_s3_error(self, mock_metadata_class, mock_s3_class, mock_dynamodb_class, mock_event, mock_context):
        """Test handling of S3 error."""
        mock_s3 = Mock()
        mock_s3.generate_presigned_upload_url.return_value = (False, None, None, 'S3 error occurred')
        mock_s3_class.return_value = mock_s3
        
        response = lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert 'error' in body
    
    @patch('src.handlers.upload_handler.DynamoDBService')
    @patch('src.handlers.upload_handler.S3Service')
    def test_dynamodb_error(self, mock_s3_class, mock_dynamodb_class, mock_event, mock_context):
        """Test handling of DynamoDB error."""
        mock_s3 = Mock()
        mock_s3.bucket_name = 'test-bucket'
        mock_s3.generate_presigned_upload_url.return_value = (True, 'https://s3.url', 'images/key', None)
        mock_s3_class.return_value = mock_s3
        
        mock_dynamodb = Mock()
        mock_dynamodb.save_metadata.return_value = (False, 'DynamoDB error')
        mock_dynamodb_class.return_value = mock_dynamodb
        
        response = lambda_handler(mock_event, mock_context)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'message' in body
    
    @patch('src.handlers.upload_handler.DynamoDBService')
    @patch('src.handlers.upload_handler.S3Service')
    def test_custom_expiry(self, mock_s3_class, mock_dynamodb_class, mock_context):
        """Test upload with custom expiry time."""
        event = {
            'headers': {'user-id': 'test-user-123'},
            'body': json.dumps({
                'filename': 'test.jpg',
                'content_type': 'image/jpeg',
                'expiry': 1800  # 30 minutes
            })
        }
        
        mock_s3 = Mock()
        mock_s3.bucket_name = 'test-bucket'
        mock_s3.generate_presigned_upload_url.return_value = (True, 'https://s3.url', 'images/key', None)
        mock_s3_class.return_value = mock_s3
        
        mock_dynamodb = Mock()
        mock_dynamodb.save_metadata.return_value = (True, None)
        mock_dynamodb_class.return_value = mock_dynamodb
        
        response = lambda_handler(event, mock_context)
        
        assert response['statusCode'] == 200
        # Verify expiry was passed to S3 service
        mock_s3.generate_presigned_upload_url.assert_called_once()
        call_kwargs = mock_s3.generate_presigned_upload_url.call_args[1]
        assert call_kwargs.get('expiry') == 1800
    
    @patch('src.handlers.upload_handler.DynamoDBService')
    @patch('src.handlers.upload_handler.S3Service')
    def test_base64_encoded_body(self, mock_s3_class, mock_dynamodb_class, mock_context):
        """Test handling of base64 encoded body."""
        import base64

        body_content = json.dumps({
            'filename': 'test.jpg',
            'content_type': 'image/jpeg'
        })
        encoded_body = base64.b64encode(body_content.encode()).decode()
        
        event = {
            'headers': {'user-id': 'test-user-123'},
            'body': encoded_body,
            'isBase64Encoded': True
        }
        
        mock_s3 = Mock()
        mock_s3.bucket_name = 'test-bucket'
        mock_s3.generate_presigned_upload_url.return_value = (True, 'https://s3.url', 'images/key', None)
        mock_s3_class.return_value = mock_s3

        mock_dynamodb = Mock()
        mock_dynamodb.save_metadata.return_value = (True, None)
        mock_dynamodb_class.return_value = mock_dynamodb

        response = lambda_handler(event, mock_context)

        assert response['statusCode'] == 200

    @patch('src.handlers.upload_handler.DynamoDBService')
    @patch('src.handlers.upload_handler.S3Service')
    def test_different_image_types(self, mock_s3_class, mock_dynamodb_class, mock_context):
        """Test different image content types."""
        content_types = ['image/png', 'image/gif', 'image/webp']
        
        for content_type in content_types:
            event = {
                'headers': {'user-id': 'test-user-123'},
                'body': json.dumps({
                    'filename': f'test.{content_type.split("/")[1]}',
                    'content_type': content_type
                })
            }
            
            mock_s3 = Mock()
            mock_s3.bucket_name = 'test-bucket'
            mock_s3.generate_presigned_upload_url.return_value = (True, 'https://s3.url', 'images/key', None)
            mock_s3_class.return_value = mock_s3
            
            mock_dynamodb = Mock()
            mock_dynamodb.save_metadata.return_value = (True, None)
            mock_dynamodb_class.return_value = mock_dynamodb
            
            response = lambda_handler(event, mock_context)
            
            assert response['statusCode'] == 201, f"Failed for {content_type}"
