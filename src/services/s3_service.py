"""
S3Service for managing image storage operations.
"""

from typing import Optional, Dict, Any, BinaryIO
import boto3
from botocore.exceptions import ClientError
from io import BytesIO

from src.config.settings import Settings
from src.utils.logger import get_logger


logger = get_logger(__name__)


class S3Service:
    """Service for S3 operations."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize S3 service.
        
        Args:
            settings: Settings instance (creates new one if not provided)
        """
        self.settings = settings or Settings()
        
        # Get S3 config
        s3_config = self.settings.get_s3_config()
        self.bucket_name = s3_config.pop('bucket_name', self.settings.S3_BUCKET_NAME)
        self.key_prefix = s3_config.pop('key_prefix', '')
        self.presigned_url_expiry = s3_config.pop('presigned_url_expiry', self.settings.S3_PRESIGNED_URL_EXPIRATION)
        
        # Create S3 client with remaining config (AWS credentials and endpoint)
        self.s3_client = boto3.client('s3', **s3_config)
        
        logger.info(f"S3Service initialized with bucket: {self.bucket_name}")
    
    def _generate_s3_key(self, user_id: str, filename: str) -> str:
        """
        Generate S3 key for the image.
        
        Args:
            user_id: User ID
            filename: Filename
        
        Returns:
            S3 key path
        """
        import uuid
        from datetime import datetime
        
        # Add timestamp and UUID to make keys unique
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        unique_id = str(uuid.uuid4())[:8]
        
        # Format: images/{user_id}/{timestamp}/{unique_id}_{filename}
        return f"{self.key_prefix}{user_id}/{timestamp}/{unique_id}_{filename}"
    
    def upload_image(
        self,
        file_content: bytes,
        user_id: str,
        filename: str,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Upload image to S3.
        
        Args:
            file_content: Image file content
            user_id: User ID
            filename: Original filename
            content_type: MIME type
            metadata: Additional metadata
        
        Returns:
            Tuple of (success, s3_key, error_message)
        """
        try:
            s3_key = self._generate_s3_key(user_id, filename)
            
            # Prepare metadata
            s3_metadata = metadata or {}
            s3_metadata['user_id'] = user_id
            s3_metadata['original_filename'] = filename
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata=s3_metadata
            )
            
            logger.info(f"Successfully uploaded image: {s3_key}")
            return True, s3_key, None
            
        except ClientError as e:
            error_msg = f"Failed to upload image: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during upload: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def generate_presigned_upload_url(
        self,
        user_id: str,
        filename: str,
        content_type: str,
        expiry: Optional[int] = None
    ) -> tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Generate presigned URL for direct upload to S3.
        
        Args:
            user_id: User ID
            filename: Original filename
            content_type: MIME type
            expiry: URL expiry in seconds (uses default if not provided)
        
        Returns:
            Tuple of (success, presigned_url, s3_key, error_message)
        """
        try:
            s3_key = self._generate_s3_key(user_id, filename)
            expiry_seconds = expiry or self.presigned_url_expiry
            
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key,
                    'ContentType': content_type
                },
                ExpiresIn=expiry_seconds
            )
            
            logger.info(f"Generated presigned upload URL for: {s3_key}")
            return True, presigned_url, s3_key, None
            
        except ClientError as e:
            error_msg = f"Failed to generate presigned upload URL: {str(e)}"
            logger.error(error_msg)
            return False, None, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error generating presigned URL: {str(e)}"
            logger.error(error_msg)
            return False, None, None, error_msg
    
    def generate_presigned_download_url(
        self,
        s3_key: str,
        expiry: Optional[int] = None
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Generate presigned URL for downloading from S3.
        
        Args:
            s3_key: S3 object key
            expiry: URL expiry in seconds (uses default if not provided)
        
        Returns:
            Tuple of (success, presigned_url, error_message)
        """
        try:
            expiry_seconds = expiry or self.presigned_url_expiry
            
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiry_seconds
            )
            
            logger.info(f"Generated presigned download URL for: {s3_key}")
            return True, presigned_url, None
            
        except ClientError as e:
            error_msg = f"Failed to generate presigned download URL: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error generating presigned URL: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def delete_image(self, s3_key: str) -> tuple[bool, Optional[str]]:
        """
        Delete image from S3.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            logger.info(f"Successfully deleted image: {s3_key}")
            return True, None
            
        except ClientError as e:
            error_msg = f"Failed to delete image: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error deleting image: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def check_image_exists(self, s3_key: str) -> tuple[bool, bool, Optional[str]]:
        """
        Check if image exists in S3.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            Tuple of (success, exists, error_message)
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True, True, None
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return True, False, None
            
            error_msg = f"Error checking image existence: {str(e)}"
            logger.error(error_msg)
            return False, False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error checking image existence: {str(e)}"
            logger.error(error_msg)
            return False, False, error_msg
    
    def check_object_exists(self, bucket: str, s3_key: str) -> tuple[bool, Optional[int], Optional[str]]:
        """
        Check if object exists in S3 and return its size.
        
        Args:
            bucket: S3 bucket name
            s3_key: S3 object key
        
        Returns:
            Tuple of (exists, size_in_bytes, error_message)
        """
        try:
            response = self.s3_client.head_object(
                Bucket=bucket,
                Key=s3_key
            )
            size = response.get('ContentLength', 0)
            return True, size, None
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False, None, None
            
            error_msg = f"Error checking object existence: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error checking object existence: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def get_image_content(self, s3_key: str) -> tuple[bool, Optional[bytes], Optional[str], Optional[str]]:
        """
        Get image content from S3.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            Tuple of (success, content, content_type, error_message)
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            content = response['Body'].read()
            content_type = response.get('ContentType', 'application/octet-stream')
            
            logger.info(f"Successfully retrieved image content: {s3_key}")
            return True, content, content_type, None
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                error_msg = f"Image not found: {s3_key}"
            else:
                error_msg = f"Failed to get image content: {str(e)}"
            
            logger.error(error_msg)
            return False, None, None, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error getting image content: {str(e)}"
            logger.error(error_msg)
            return False, None, None, error_msg
    
    def get_image_metadata(self, s3_key: str) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Get image metadata from S3.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            Tuple of (success, metadata_dict, error_message)
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            metadata = {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified').isoformat() if response.get('LastModified') else None,
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {})
            }
            
            logger.info(f"Successfully retrieved metadata for: {s3_key}")
            return True, metadata, None
            
        except ClientError as e:
            error_msg = f"Failed to get image metadata: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error getting image metadata: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
