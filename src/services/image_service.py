"""
ImageService orchestration layer.
Coordinates S3 and DynamoDB operations.
Note: With presigned URLs, files never go through Lambda, so no image processing needed.
"""

from typing import Optional, List, Dict, Any, Tuple

from src.config.settings import Settings
from src.models.image_metadata import ImageMetadata
from src.services.s3_service import S3Service
from src.services.dynamodb_service import DynamoDBService
from src.utils.logger import get_logger
from src.utils.validators import (
    validate_content_type,
    validate_file_size,
    validate_user_id,
    validate_tags,
    validate_description,
    sanitize_filename
)


logger = get_logger(__name__)


class ImageService:
    """
    Orchestration service for image operations.
    Coordinates S3 and DynamoDB with transaction-like rollback.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize ImageService.
        
        Args:
            settings: Settings instance (creates new one if not provided)
        """
        self.settings = settings or Settings()
        self.s3_service = S3Service(self.settings)
        self.dynamodb_service = DynamoDBService(self.settings)
        
        logger.info("ImageService initialized")
    
    # NOTE: upload_image method is NOT USED with presigned URL approach
    # Files are uploaded directly to S3 from client, Lambda only generates presigned URLs
    # Keeping this method commented out for reference/future use
    #
    # def upload_image(self, file_content: bytes, ...):
    #     """Legacy method - not used with presigned URLs"""
    #     pass
    
    def get_image(
        self,
        image_id: str,
        user_id: str
    ) -> tuple[bool, Optional[ImageMetadata], Optional[bytes], Optional[str]]:
        """
        Get image metadata and content.
        
        Args:
            image_id: Image ID
            user_id: User ID (for authorization)
        
        Returns:
            Tuple of (success, metadata, content, error_message)
        """
        try:
            # Get metadata
            success, metadata, error = self.dynamodb_service.get_metadata(image_id)
            if not success:
                return False, None, None, f"Failed to get metadata: {error}"
            
            if not metadata:
                return False, None, None, "Image not found"
            
            # Check authorization
            if metadata.user_id != user_id:
                return False, None, None, "Unauthorized access"
            
            # Check status
            if metadata.status == 'deleted':
                return False, None, None, "Image has been deleted"
            
            # Get content from S3
            success, content, _, error = self.s3_service.get_image_content(metadata.s3_key)
            if not success:
                return False, None, None, f"Failed to get image content: {error}"
            
            logger.info(f"Successfully retrieved image: {image_id}")
            return True, metadata, content, None
            
        except Exception as e:
            error_msg = f"Unexpected error getting image: {str(e)}"
            logger.error(error_msg)
            return False, None, None, error_msg
    
    def get_image_metadata(
        self,
        image_id: str,
        user_id: str
    ) -> tuple[bool, Optional[ImageMetadata], Optional[str]]:
        """
        Get image metadata only.
        
        Args:
            image_id: Image ID
            user_id: User ID (for authorization)
        
        Returns:
            Tuple of (success, metadata, error_message)
        """
        try:
            # Get metadata
            success, metadata, error = self.dynamodb_service.get_metadata(image_id)
            if not success:
                return False, None, f"Failed to get metadata: {error}"
            
            if not metadata:
                return False, None, "Image not found"
            
            # Check authorization
            if metadata.user_id != user_id:
                return False, None, "Unauthorized access"
            
            logger.info(f"Successfully retrieved metadata: {image_id}")
            return True, metadata, None
            
        except Exception as e:
            error_msg = f"Unexpected error getting metadata: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def list_user_images(
        self,
        user_id: str,
        status: Optional[str] = 'active',
        limit: int = 100,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, List[ImageMetadata], Optional[Dict[str, Any]], Optional[str]]:
        """
        List images for a user.
        
        Args:
            user_id: User ID
            status: Status filter (default: 'active')
            limit: Maximum number of items
            last_evaluated_key: Pagination token
        
        Returns:
            Tuple of (success, metadata_list, next_key, error_message)
        """
        try:
            success, metadata_list, next_key, error = self.dynamodb_service.query_by_user(
                user_id=user_id,
                status=status,
                limit=limit,
                last_evaluated_key=last_evaluated_key
            )
            
            if not success:
                return False, [], None, f"Failed to list images: {error}"
            
            logger.info(f"Successfully listed {len(metadata_list)} images for user: {user_id}")
            return True, metadata_list, next_key, None
            
        except Exception as e:
            error_msg = f"Unexpected error listing images: {str(e)}"
            logger.error(error_msg)
            return False, [], None, error_msg
    
    def search_images(
        self,
        user_id: str,
        tags: Optional[List[str]] = None,
        content_type: Optional[str] = None,
        status: Optional[str] = 'active',
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        limit: int = 100,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, List[ImageMetadata], Optional[Dict[str, Any]], Optional[str]]:
        """
        Search images with filters.
        
        Args:
            user_id: User ID
            tags: Tag filters
            content_type: Content type filter
            status: Status filter
            min_size: Minimum file size
            max_size: Maximum file size
            limit: Maximum number of items
            last_evaluated_key: Pagination token
        
        Returns:
            Tuple of (success, metadata_list, next_key, error_message)
        """
        try:
            # Build filters
            filters = {}
            if status:
                filters['status'] = status
            if tags:
                filters['tags'] = tags
            if content_type:
                filters['content_type'] = content_type
            if min_size:
                filters['min_size'] = min_size
            if max_size:
                filters['max_size'] = max_size
            
            success, metadata_list, next_key, error = self.dynamodb_service.query_with_filters(
                user_id=user_id,
                filters=filters,
                limit=limit,
                last_evaluated_key=last_evaluated_key
            )
            
            if not success:
                return False, [], None, f"Failed to search images: {error}"
            
            logger.info(f"Successfully searched {len(metadata_list)} images for user: {user_id}")
            return True, metadata_list, next_key, None
            
        except Exception as e:
            error_msg = f"Unexpected error searching images: {str(e)}"
            logger.error(error_msg)
            return False, [], None, error_msg
    
    def update_image_metadata(
        self,
        image_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> tuple[bool, Optional[ImageMetadata], Optional[str]]:
        """
        Update image metadata.
        
        Args:
            image_id: Image ID
            user_id: User ID (for authorization)
            updates: Dictionary of fields to update
        
        Returns:
            Tuple of (success, updated_metadata, error_message)
        """
        try:
            # Get current metadata to check authorization
            success, metadata, error = self.dynamodb_service.get_metadata(image_id)
            if not success:
                return False, None, f"Failed to get metadata: {error}"
            
            if not metadata:
                return False, None, "Image not found"
            
            # Check authorization
            if metadata.user_id != user_id:
                return False, None, "Unauthorized access"
            
            # Validate updates
            if 'tags' in updates:
                is_valid, error = validate_tags(updates['tags'])
                if not is_valid:
                    return False, None, f"Invalid tags: {error}"
            
            if 'description' in updates:
                is_valid, error = validate_description(updates['description'])
                if not is_valid:
                    return False, None, f"Invalid description: {error}"
            
            # Prevent updating critical fields
            protected_fields = ['image_id', 'user_id', 's3_key', 's3_bucket', 'upload_timestamp']
            for field in protected_fields:
                if field in updates:
                    return False, None, f"Cannot update protected field: {field}"
            
            # Update metadata
            success, updated_metadata, error = self.dynamodb_service.update_metadata(
                image_id=image_id,
                updates=updates
            )
            
            if not success:
                return False, None, f"Failed to update metadata: {error}"
            
            logger.info(f"Successfully updated metadata for image: {image_id}")
            return True, updated_metadata, None
            
        except Exception as e:
            error_msg = f"Unexpected error updating metadata: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def delete_image(
        self,
        image_id: str,
        user_id: str,
        soft_delete: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        Delete image (soft or hard delete).
        
        Args:
            image_id: Image ID
            user_id: User ID (for authorization)
            soft_delete: If True, mark as deleted; if False, remove from S3 and DynamoDB
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get metadata to check authorization
            success, metadata, error = self.dynamodb_service.get_metadata(image_id)
            if not success:
                return False, f"Failed to get metadata: {error}"
            
            if not metadata:
                return False, "Image not found"
            
            # Check authorization
            if metadata.user_id != user_id:
                return False, "Unauthorized access"
            
            if soft_delete:
                # Soft delete: Update status
                success, error = self.dynamodb_service.update_metadata(
                    image_id=image_id,
                    updates={'status': 'deleted'}
                )
                
                if not success:
                    return False, f"Failed to mark image as deleted: {error}"
                
                logger.info(f"Successfully soft-deleted image: {image_id}")
                return True, None
            else:
                # Hard delete: Remove from S3 and DynamoDB
                # Delete from S3 first
                success, error = self.s3_service.delete_image(metadata.s3_key)
                if not success:
                    logger.warning(f"Failed to delete from S3: {error}")
                    # Continue with DynamoDB deletion anyway
                
                # Delete from DynamoDB
                success, error = self.dynamodb_service.delete_metadata(image_id)
                if not success:
                    return False, f"Failed to delete metadata: {error}"
                
                logger.info(f"Successfully hard-deleted image: {image_id}")
                return True, None
            
        except Exception as e:
            error_msg = f"Unexpected error deleting image: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def generate_presigned_url(
        self,
        image_id: str,
        user_id: str,
        expiry: Optional[int] = None
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Generate presigned URL for image download.
        
        Args:
            image_id: Image ID
            user_id: User ID (for authorization)
            expiry: URL expiry in seconds
        
        Returns:
            Tuple of (success, presigned_url, error_message)
        """
        try:
            # Get metadata to check authorization
            success, metadata, error = self.dynamodb_service.get_metadata(image_id)
            if not success:
                return False, None, f"Failed to get metadata: {error}"
            
            if not metadata:
                return False, None, "Image not found"
            
            # Check authorization
            if metadata.user_id != user_id:
                return False, None, "Unauthorized access"
            
            # Check status
            if metadata.status == 'deleted':
                return False, None, "Image has been deleted"
            
            # Generate presigned URL
            success, presigned_url, error = self.s3_service.generate_presigned_download_url(
                s3_key=metadata.s3_key,
                expiry=expiry
            )
            
            if not success:
                return False, None, f"Failed to generate presigned URL: {error}"
            
            logger.info(f"Successfully generated presigned URL for image: {image_id}")
            return True, presigned_url, None
            
        except Exception as e:
            error_msg = f"Unexpected error generating presigned URL: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
