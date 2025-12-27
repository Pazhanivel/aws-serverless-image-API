"""
ImageMetadata data model.
Represents image metadata stored in DynamoDB.
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


@dataclass
class ImageMetadata:
    """
    Image metadata model.
    
    Attributes:
        image_id: Unique identifier (UUID)
        user_id: User who uploaded the image
        filename: Original filename
        content_type: MIME type (e.g., image/jpeg)
        size: File size in bytes
        s3_key: S3 object key
        s3_bucket: S3 bucket name
        upload_timestamp: ISO 8601 timestamp
        tags: List of tags
        description: Optional description
        width: Image width in pixels
        height: Image height in pixels
        status: Status (active, deleted, processing)
        metadata: Additional metadata dictionary
    """
    
    image_id: str
    user_id: str
    filename: str
    content_type: str
    size: int
    s3_key: str
    s3_bucket: str
    upload_timestamp: str
    tags: List[str]
    description: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    status: str = 'active'
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(
        cls,
        user_id: str,
        filename: str,
        content_type: str,
        size: int,
        s3_key: str,
        s3_bucket: str,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ImageMetadata':
        """
        Factory method to create a new ImageMetadata instance.
        
        Args:
            user_id: User who uploaded the image
            filename: Original filename
            content_type: MIME type
            size: File size in bytes
            s3_key: S3 object key
            s3_bucket: S3 bucket name
            tags: List of tags (optional)
            description: Description text (optional)
            width: Image width (optional)
            height: Image height (optional)
            metadata: Additional metadata (optional)
        
        Returns:
            New ImageMetadata instance
        """
        return cls(
            image_id=str(uuid.uuid4()),
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            size=size,
            s3_key=s3_key,
            s3_bucket=s3_bucket,
            upload_timestamp=datetime.utcnow().isoformat() + 'Z',
            tags=tags or [],
            description=description,
            width=width,
            height=height,
            status='active',
            metadata=metadata or {}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        data = asdict(self)
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}
    
    def to_dynamodb(self) -> Dict[str, Any]:
        """
        Convert to DynamoDB item format.
        
        Returns:
            Dictionary formatted for DynamoDB
        """
        item = self.to_dict()
        
        # DynamoDB doesn't support empty strings in certain contexts
        # Convert empty strings to None
        for key, value in item.items():
            if isinstance(value, str) and not value:
                item[key] = None
        
        # Ensure tags is always a list
        if 'tags' not in item:
            item['tags'] = []
        
        # Ensure metadata is always a dict
        if 'metadata' not in item or item['metadata'] is None:
            item['metadata'] = {}
        
        return item
    
    @classmethod
    def from_dynamodb(cls, item: Dict[str, Any]) -> 'ImageMetadata':
        """
        Create ImageMetadata from DynamoDB item.
        
        Args:
            item: DynamoDB item dictionary
        
        Returns:
            ImageMetadata instance
        """
        return cls(
            image_id=item['image_id'],
            user_id=item['user_id'],
            filename=item['filename'],
            content_type=item['content_type'],
            size=int(item['size']),
            s3_key=item['s3_key'],
            s3_bucket=item['s3_bucket'],
            upload_timestamp=item['upload_timestamp'],
            tags=item.get('tags', []),
            description=item.get('description'),
            width=int(item['width']) if item.get('width') else None,
            height=int(item['height']) if item.get('height') else None,
            status=item.get('status', 'active'),
            metadata=item.get('metadata', {})
        )
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the image metadata.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        from src.utils.validators import (
            validate_user_id,
            validate_content_type,
            validate_file_size,
            validate_tags,
            validate_description
        )
        
        # Validate user_id
        is_valid, error = validate_user_id(self.user_id)
        if not is_valid:
            return False, f"Invalid user_id: {error}"
        
        # Validate content_type
        is_valid, error = validate_content_type(self.content_type)
        if not is_valid:
            return False, f"Invalid content_type: {error}"
        
        # Validate file size
        is_valid, error = validate_file_size(self.size)
        if not is_valid:
            return False, f"Invalid size: {error}"
        
        # Validate tags
        if self.tags:
            is_valid, error = validate_tags(self.tags)
            if not is_valid:
                return False, f"Invalid tags: {error}"
        
        # Validate description
        if self.description:
            is_valid, error = validate_description(self.description)
            if not is_valid:
                return False, f"Invalid description: {error}"
        
        # Validate dimensions
        if self.width is not None and self.width <= 0:
            return False, "Width must be greater than 0"
        
        if self.height is not None and self.height <= 0:
            return False, "Height must be greater than 0"
        
        # Validate status
        valid_statuses = ['active', 'deleted', 'processing', 'error']
        if self.status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        
        return True, None
    
    def update(self, **kwargs) -> 'ImageMetadata':
        """
        Create a new instance with updated fields.
        
        Args:
            **kwargs: Fields to update
        
        Returns:
            New ImageMetadata instance with updates
        """
        data = self.to_dict()
        data.update(kwargs)
        return ImageMetadata(**data)
    
    def mark_deleted(self) -> 'ImageMetadata':
        """
        Mark the image as deleted (soft delete).
        
        Returns:
            New ImageMetadata instance with deleted status
        """
        return self.update(status='deleted')
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ImageMetadata(image_id='{self.image_id}', user_id='{self.user_id}', filename='{self.filename}')"
