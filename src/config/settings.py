"""
Application configuration settings for the image service.
Handles environment variables and AWS service configuration.
"""

import os
from typing import Optional


class Settings:
    """Application configuration settings"""

    # AWS Configuration
    AWS_REGION: str = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    AWS_PROFILE: str = os.getenv('AWS_PROFILE', 'localstack')
    
    # LocalStack Configuration
    LOCALSTACK_ENDPOINT: str = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
    USE_LOCALSTACK: bool = os.getenv('USE_LOCALSTACK', 'true').lower() == 'true'
    
    # S3 Configuration
    S3_BUCKET_NAME: str = os.getenv('S3_BUCKET_NAME', 'image-storage-bucket')
    S3_PRESIGNED_URL_EXPIRATION: int = int(os.getenv('S3_PRESIGNED_URL_EXPIRATION', '900'))  # 15 minutes
    
    # DynamoDB Configuration
    DYNAMODB_TABLE_NAME: str = os.getenv('DYNAMODB_TABLE_NAME', 'images')
    DYNAMODB_USER_INDEX: str = 'UserIndex'
    DYNAMODB_STATUS_INDEX: str = 'StatusIndex'
    
    # Image Validation
    # Support both MAX_IMAGE_SIZE and legacy MAX_FILE_SIZE env vars
    MAX_IMAGE_SIZE: int = int(os.getenv('MAX_IMAGE_SIZE', os.getenv('MAX_FILE_SIZE', str(10 * 1024 * 1024))))  # 10 MB
    # Allow overriding content types via ALLOWED_CONTENT_TYPES env (CSV)
    ALLOWED_CONTENT_TYPES: list = [ct.strip() for ct in os.getenv(
        'ALLOWED_CONTENT_TYPES',
        'image/jpeg,image/jpg,image/png,image/gif,image/webp'
    ).split(',') if ct.strip()]
    ALLOWED_EXTENSIONS: list = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100
    
    # Application
    APP_NAME: str = 'image-service'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def get_aws_config(cls) -> dict:
        """Get AWS service configuration"""
        config = {
            'region_name': cls.AWS_REGION
        }
        
        if cls.USE_LOCALSTACK:
            config['endpoint_url'] = cls.LOCALSTACK_ENDPOINT
            config['aws_access_key_id'] = 'test'
            config['aws_secret_access_key'] = 'test'
        
        return config

    @classmethod
    def get_s3_config(cls) -> dict:
        """Get S3 specific configuration"""
        config = cls.get_aws_config()
        config['bucket_name'] = cls.S3_BUCKET_NAME
        config['presigned_url_expiry'] = cls.S3_PRESIGNED_URL_EXPIRATION
        config['key_prefix'] = ''  # No prefix for now
        return config

    @classmethod
    def get_dynamodb_config(cls) -> dict:
        """Get DynamoDB specific configuration"""
        config = cls.get_aws_config()
        config['table_name'] = cls.DYNAMODB_TABLE_NAME
        config['user_index'] = cls.DYNAMODB_USER_INDEX
        config['status_index'] = cls.DYNAMODB_STATUS_INDEX
        return config

    @classmethod
    def validate_content_type(cls, content_type: str) -> bool:
        """Check if content type is allowed"""
        return content_type.lower() in [ct.lower() for ct in cls.ALLOWED_CONTENT_TYPES]

    @classmethod
    def validate_file_size(cls, size: int) -> bool:
        """Check if file size is within limits"""
        return 0 < size <= cls.MAX_IMAGE_SIZE


# Global settings instance
settings = Settings()