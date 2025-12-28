"""
Unit tests for S3Service, DynamoDBService, and ImageService.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from src.services.s3_service import S3Service
from src.services.dynamodb_service import DynamoDBService
from src.services.image_service import ImageService
from src.models.image_metadata import ImageMetadata


class TestS3Service:
    """Tests for S3Service."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.get_s3_config.return_value = {
            'bucket_name': 'test-bucket',
            'key_prefix': 'images/',
            'presigned_url_expiry': 900
        }
        settings.get_aws_config.return_value = {
            'endpoint_url': 'http://localhost:4566',
            'region': 'us-east-1',
            'access_key': 'test',
            'secret_key': 'test'
        }
        return settings
    
    @patch('src.services.s3_service.boto3.client')
    def test_initialization(self, mock_boto_client, mock_settings):
        """Test S3Service initialization."""
        service = S3Service(mock_settings)
        
        assert service.bucket_name == 'test-bucket'
        assert service.key_prefix == 'images/'
        mock_boto_client.assert_called_once()
    
    @patch('src.services.s3_service.boto3.client')
    def test_generate_s3_key(self, mock_boto_client, mock_settings):
        """Test S3 key generation."""
        service = S3Service(mock_settings)
        
        key = service._generate_s3_key('user123', 'photo.jpg')
        
        assert key.startswith('images/user123/')
        assert key.endswith('_photo.jpg')
    
    @patch('src.services.s3_service.boto3.client')
    def test_upload_image_success(self, mock_boto_client, mock_settings):
        """Test successful image upload."""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        service = S3Service(mock_settings)
        
        success, s3_key, error = service.upload_image(
            file_content=b'test image data',
            user_id='user123',
            filename='test.jpg',
            content_type='image/jpeg'
        )
        
        assert success is True
        assert s3_key is not None
        assert error is None
        mock_s3.put_object.assert_called_once()
    
    @patch('src.services.s3_service.boto3.client')
    def test_upload_image_client_error(self, mock_boto_client, mock_settings):
        """Test upload with ClientError."""
        mock_s3 = Mock()
        mock_s3.put_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}},
            'PutObject'
        )
        mock_boto_client.return_value = mock_s3
        
        service = S3Service(mock_settings)
        
        success, s3_key, error = service.upload_image(
            file_content=b'test',
            user_id='user123',
            filename='test.jpg',
            content_type='image/jpeg'
        )
        
        assert success is False
        assert error is not None
    
    @patch('src.services.s3_service.boto3.client')
    def test_generate_presigned_upload_url(self, mock_boto_client, mock_settings):
        """Test presigned upload URL generation."""
        mock_s3 = Mock()
        mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/test-url'
        mock_boto_client.return_value = mock_s3
        
        service = S3Service(mock_settings)
        
        success, url, s3_key, error = service.generate_presigned_upload_url(
            user_id='user123',
            filename='test.jpg',
            content_type='image/jpeg'
        )
        
        assert success is True
        assert url == 'https://s3.amazonaws.com/test-url'
        assert s3_key is not None
        assert error is None
    
    @patch('src.services.s3_service.boto3.client')
    def test_generate_presigned_download_url(self, mock_boto_client, mock_settings):
        """Test presigned download URL generation."""
        mock_s3 = Mock()
        mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/download-url'
        mock_boto_client.return_value = mock_s3
        
        service = S3Service(mock_settings)
        
        success, url, error = service.generate_presigned_download_url(
            s3_key='images/user123/test.jpg'
        )
        
        assert success is True
        assert url == 'https://s3.amazonaws.com/download-url'
        assert error is None
    
    @patch('src.services.s3_service.boto3.client')
    def test_delete_image_success(self, mock_boto_client, mock_settings):
        """Test successful image deletion."""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        service = S3Service(mock_settings)
        
        success, error = service.delete_image('images/user123/test.jpg')
        
        assert success is True
        assert error is None
        mock_s3.delete_object.assert_called_once()
    
    @patch('src.services.s3_service.boto3.client')
    def test_get_image_content_success(self, mock_boto_client, mock_settings):
        """Test successful image content retrieval."""
        mock_s3 = Mock()
        mock_response = {
            'Body': Mock(read=Mock(return_value=b'image data')),
            'ContentType': 'image/jpeg'
        }
        mock_s3.get_object.return_value = mock_response
        mock_boto_client.return_value = mock_s3
        
        service = S3Service(mock_settings)
        
        success, content, content_type, error = service.get_image_content('images/user123/test.jpg')
        
        assert success is True
        assert content == b'image data'
        assert content_type == 'image/jpeg'
        assert error is None


class TestDynamoDBService:
    """Tests for DynamoDBService."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.get_dynamodb_config.return_value = {
            'table_name': 'test-images',
            'user_index': 'UserIndex',
            'status_index': 'StatusIndex'
        }
        settings.get_aws_config.return_value = {
            'endpoint_url': 'http://localhost:4566',
            'region': 'us-east-1',
            'access_key': 'test',
            'secret_key': 'test'
        }
        return settings
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample ImageMetadata."""
        return ImageMetadata.create(
            user_id='user123',
            filename='test.jpg',
            content_type='image/jpeg',
            size=1024,
            s3_key='images/user123/test.jpg',
            s3_bucket='test-bucket'
        )
    
    @patch('src.services.dynamodb_service.boto3.resource')
    def test_initialization(self, mock_boto_resource, mock_settings):
        """Test DynamoDBService initialization."""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_dynamodb
        
        service = DynamoDBService(mock_settings)
        
        assert service.table_name == 'test-images'
        assert service.user_index == 'UserIndex'
        mock_boto_resource.assert_called_once()
    
    @patch('src.services.dynamodb_service.boto3.resource')
    def test_save_metadata_success(self, mock_boto_resource, mock_settings, sample_metadata):
        """Test successful metadata save."""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_dynamodb
        
        service = DynamoDBService(mock_settings)
        
        success, error = service.save_metadata(sample_metadata)
        
        assert success is True
        assert error is None
        mock_table.put_item.assert_called_once()
    
    @patch('src.services.dynamodb_service.boto3.resource')
    def test_save_metadata_client_error(self, mock_boto_resource, mock_settings, sample_metadata):
        """Test save metadata with ClientError."""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_table.put_item.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid item'}},
            'PutItem'
        )
        mock_dynamodb.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_dynamodb
        
        service = DynamoDBService(mock_settings)
        
        success, error = service.save_metadata(sample_metadata)
        
        assert success is False
        assert error is not None
    
    @patch('src.services.dynamodb_service.boto3.resource')
    def test_get_metadata_success(self, mock_boto_resource, mock_settings):
        """Test successful metadata retrieval."""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'image_id': 'test-id',
                'user_id': 'user123',
                'filename': 'test.jpg',
                'content_type': 'image/jpeg',
                'size': 1024,
                's3_key': 'images/test.jpg',
                's3_bucket': 'test-bucket',
                'upload_timestamp': '2024-01-01T00:00:00Z',
                'tags': ['test'],
                'status': 'active'
            }
        }
        mock_dynamodb.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_dynamodb
        
        service = DynamoDBService(mock_settings)
        
        success, metadata, error = service.get_metadata('test-id')
        
        assert success is True
        assert metadata is not None
        assert metadata.image_id == 'test-id'
        assert error is None
    
    @patch('src.services.dynamodb_service.boto3.resource')
    def test_get_metadata_not_found(self, mock_boto_resource, mock_settings):
        """Test metadata not found."""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_table.get_item.return_value = {}
        mock_dynamodb.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_dynamodb
        
        service = DynamoDBService(mock_settings)
        
        success, metadata, error = service.get_metadata('nonexistent-id')
        
        assert success is True
        assert metadata is None
        assert error is None
    
    @patch('src.services.dynamodb_service.boto3.resource')
    def test_delete_metadata_success(self, mock_boto_resource, mock_settings):
        """Test successful metadata deletion."""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_dynamodb
        
        service = DynamoDBService(mock_settings)
        
        success, error = service.delete_metadata('test-id')
        
        assert success is True
        assert error is None
        mock_table.delete_item.assert_called_once()
    
    @patch('src.services.dynamodb_service.boto3.resource')
    def test_query_by_user(self, mock_boto_resource, mock_settings):
        """Test query by user_id."""
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_table.query.return_value = {
            'Items': [
                {
                    'image_id': 'img1',
                    'user_id': 'user123',
                    'filename': 'test1.jpg',
                    'content_type': 'image/jpeg',
                    'size': 1024,
                    's3_key': 'key1',
                    's3_bucket': 'bucket',
                    'upload_timestamp': '2024-01-01T00:00:00Z',
                    'tags': [],
                    'status': 'active'
                }
            ]
        }
        mock_dynamodb.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_dynamodb
        
        service = DynamoDBService(mock_settings)
        
        success, items, next_key, error = service.query_by_user('user123')
        
        assert success is True
        assert len(items) == 1
        assert items[0].image_id == 'img1'
        assert error is None


class TestImageService:
    """Tests for ImageService."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.get_s3_config.return_value = {
            'bucket_name': 'test-bucket',
            'key_prefix': 'images/',
            'presigned_url_expiry': 900
        }
        settings.get_dynamodb_config.return_value = {
            'table_name': 'test-images',
            'user_index': 'UserIndex',
            'status_index': 'StatusIndex'
        }
        settings.get_aws_config.return_value = {
            'endpoint_url': 'http://localhost:4566',
            'region': 'us-east-1',
            'access_key': 'test',
            'secret_key': 'test'
        }
        return settings
    
    @patch('src.services.image_service.DynamoDBService')
    @patch('src.services.image_service.S3Service')
    def test_initialization(self, mock_s3_class, mock_dynamodb_class, mock_settings):
        """Test ImageService initialization."""
        service = ImageService(mock_settings)
        
        assert service.s3_service is not None
        assert service.dynamodb_service is not None
    
    @patch('src.services.image_service.DynamoDBService')
    @patch('src.services.image_service.S3Service')
    def test_get_image_metadata_success(self, mock_s3_class, mock_dynamodb_class, mock_settings):
        """Test successful metadata retrieval."""
        mock_dynamodb = Mock()
        mock_metadata = Mock()
        mock_metadata.user_id = 'user123'
        mock_dynamodb.get_metadata.return_value = (True, mock_metadata, None)
        mock_dynamodb_class.return_value = mock_dynamodb
        
        service = ImageService(mock_settings)
        
        success, metadata, error = service.get_image_metadata('img-id', 'user123')
        
        assert success is True
        assert metadata is not None
        assert error is None
    
    @patch('src.services.image_service.DynamoDBService')
    @patch('src.services.image_service.S3Service')
    def test_get_image_metadata_unauthorized(self, mock_s3_class, mock_dynamodb_class, mock_settings):
        """Test unauthorized access."""
        mock_dynamodb = Mock()
        mock_metadata = Mock()
        mock_metadata.user_id = 'user123'
        mock_dynamodb.get_metadata.return_value = (True, mock_metadata, None)
        mock_dynamodb_class.return_value = mock_dynamodb
        
        service = ImageService(mock_settings)
        
        success, metadata, error = service.get_image_metadata('img-id', 'different-user')
        
        assert success is False
        assert 'Unauthorized' in error
    
    @patch('src.services.image_service.DynamoDBService')
    @patch('src.services.image_service.S3Service')
    def test_delete_image_soft(self, mock_s3_class, mock_dynamodb_class, mock_settings):
        """Test soft delete."""
        mock_dynamodb = Mock()
        mock_metadata = Mock()
        mock_metadata.user_id = 'user123'
        mock_dynamodb.get_metadata.return_value = (True, mock_metadata, None)
        mock_dynamodb.update_metadata.return_value = (True, None)  # Fixed: returns 2 values
        mock_dynamodb_class.return_value = mock_dynamodb
        
        service = ImageService(mock_settings)
        
        success, error = service.delete_image('img-id', 'user123', soft_delete=True)
        
        assert success is True
        assert error is None
        mock_dynamodb.update_metadata.assert_called_once()
    
    @patch('src.services.image_service.DynamoDBService')
    @patch('src.services.image_service.S3Service')
    def test_delete_image_hard(self, mock_s3_class, mock_dynamodb_class, mock_settings):
        """Test hard delete."""
        mock_s3 = Mock()
        mock_s3.delete_image.return_value = (True, None)
        mock_s3_class.return_value = mock_s3
        
        mock_dynamodb = Mock()
        mock_metadata = Mock()
        mock_metadata.user_id = 'user123'
        mock_metadata.s3_key = 'images/test.jpg'
        mock_dynamodb.get_metadata.return_value = (True, mock_metadata, None)
        mock_dynamodb.delete_metadata.return_value = (True, None)
        mock_dynamodb_class.return_value = mock_dynamodb
        
        service = ImageService(mock_settings)
        
        success, error = service.delete_image('img-id', 'user123', soft_delete=False)
        
        assert success is True
        assert error is None
        mock_s3.delete_image.assert_called_once()
        mock_dynamodb.delete_metadata.assert_called_once()
    
    @patch('src.services.image_service.DynamoDBService')
    @patch('src.services.image_service.S3Service')
    def test_generate_presigned_url_success(self, mock_s3_class, mock_dynamodb_class, mock_settings):
        """Test presigned URL generation."""
        mock_s3 = Mock()
        mock_s3.generate_presigned_download_url.return_value = (True, 'https://s3.url', None)
        mock_s3_class.return_value = mock_s3
        
        mock_dynamodb = Mock()
        mock_metadata = Mock()
        mock_metadata.user_id = 'user123'
        mock_metadata.status = 'active'
        mock_metadata.s3_key = 'images/test.jpg'
        mock_dynamodb.get_metadata.return_value = (True, mock_metadata, None)
        mock_dynamodb_class.return_value = mock_dynamodb
        
        service = ImageService(mock_settings)
        
        success, url, error = service.generate_presigned_url('img-id', 'user123')
        
        assert success is True
        assert url == 'https://s3.url'
        assert error is None
    
    @patch('src.services.image_service.DynamoDBService')
    @patch('src.services.image_service.S3Service')
    def test_list_user_images(self, mock_s3_class, mock_dynamodb_class, mock_settings):
        """Test listing user images."""
        mock_dynamodb = Mock()
        mock_metadata = Mock()
        mock_dynamodb.query_by_user.return_value = (True, [mock_metadata], None, None)
        mock_dynamodb_class.return_value = mock_dynamodb
        
        service = ImageService(mock_settings)
        
        success, images, next_key, error = service.list_user_images('user123')
        
        assert success is True
        assert len(images) == 1
        assert error is None
