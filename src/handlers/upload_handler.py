"""
Lambda handler for uploading images.
Client-side direct upload to S3 using presigned URLs.

Flow:
1. Client requests presigned URL with image metadata
2. Lambda creates DynamoDB entry with 'processing' status
3. Lambda generates presigned S3 URL and returns it
4. Client uploads image directly to S3 using PUT request
5. (Optional) Client calls /images/{image_id}/complete to update status to 'active'

This approach avoids Lambda's 6MB payload limit and is much more efficient.
"""

import json
import base64
from typing import Dict, Any
from datetime import datetime
import uuid

from src.models.image_metadata import ImageMetadata
from src.services.s3_service import S3Service
from src.services.dynamodb_service import DynamoDBService
from src.utils.response import success_response, error_response, validation_error_response, internal_error_response
from src.utils.logger import get_logger
from src.utils.validators import (
    validate_user_id,
    validate_content_type,
    validate_tags,
    validate_description,
    sanitize_filename
)


logger = get_logger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for image upload initiation.
    
    Returns presigned S3 URL for direct client upload.
    
    Request body (JSON):
    {
        "filename": "photo.jpg",
        "content_type": "image/jpeg",
        "tags": ["vacation", "beach"],       // Optional
        "description": "My vacation photo",   // Optional
        "expiry": 900                         // Optional, default 15 minutes
    }
    
    Headers:
    - user-id: User ID (required)
    
    Response:
    {
        "success": true,
        "data": {
            "image_id": "uuid",
            "presigned_url": "https://s3.amazonaws.com/...",
            "s3_key": "images/user123/...",
            "expiry_seconds": 900,
            "upload_method": "PUT",
            "headers": {"Content-Type": "image/jpeg"},
            "instructions": {
                "method": "PUT",
                "url": "...",
                "note": "After upload, optionally call PATCH /images/{image_id}/complete"
            }
        }
    }
    
    Args:
        event: Lambda event
        context: Lambda context
    
    Returns:
        API Gateway response with presigned URL
    """
    try:
        logger.info("Upload handler invoked - presigned URL generation")
        
        # Extract headers
        headers = event.get('headers', {}) or {}
        user_id = headers.get('user-id') or headers.get('User-Id', '')
        
        # Validate user_id
        if not user_id:
            return validation_error_response("user-id header is required")
        
        is_valid, error = validate_user_id(user_id)
        if not is_valid:
            return validation_error_response(f"Invalid user-id: {error}")
        
        # Parse request body
        body = event.get('body', '')
        is_base64 = event.get('isBase64Encoded', False)
        
        if not body:
            return validation_error_response("Request body is required")
        
        try:
            if is_base64:
                body = base64.b64decode(body).decode('utf-8')
            
            data = json.loads(body)
        except json.JSONDecodeError as e:
            return validation_error_response(f"Invalid JSON: {str(e)}")
        
        # Extract and validate required fields
        if 'filename' not in data:
            return validation_error_response("Missing 'filename' field")
        
        if 'content_type' not in data:
            return validation_error_response("Missing 'content_type' field")
        
        filename = sanitize_filename(data['filename'])
        content_type = data['content_type']
        
        # Validate content type
        is_valid, error = validate_content_type(content_type)
        if not is_valid:
            return validation_error_response(f"Invalid content_type: {error}")
        
        # Extract optional fields
        tags = data.get('tags', [])
        description = data.get('description')
        expiry = data.get('expiry', 900)  # Default 15 minutes
        
        # Validate tags if provided
        if tags:
            is_valid, error = validate_tags(tags)
            if not is_valid:
                return validation_error_response(f"Invalid tags: {error}")
        
        # Validate description if provided
        if description:
            is_valid, error = validate_description(description)
            if not is_valid:
                return validation_error_response(f"Invalid description: {error}")
        
        # Generate presigned URL
        s3_service = S3Service()
        success, presigned_url, s3_key, error = s3_service.generate_presigned_upload_url(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            expiry=expiry
        )
        
        if not success:
            return error_response(f"Failed to generate presigned URL: {error}")
        
        # Create metadata entry with 'processing' status
        # This reserves the image_id and tracks the pending upload
        image_id = str(uuid.uuid4())
        metadata = ImageMetadata(
            image_id=image_id,
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            size=0,  # Will be updated when upload completes
            s3_key=s3_key,
            s3_bucket=s3_service.bucket_name,
            upload_timestamp=datetime.utcnow().isoformat() + 'Z',
            tags=tags,
            description=description,
            width=None,  # Will be updated after upload if needed
            height=None,  # Will be updated after upload if needed
            status='processing',  # Set to processing until upload completes
            metadata={'presigned_upload': True}
        )
        
        # Save metadata to DynamoDB (skip validation for processing status with size=0)
        dynamodb_service = DynamoDBService()
        success, error = dynamodb_service.save_metadata(metadata, skip_validation=True)
        
        if not success:
            logger.error(f"Failed to save metadata: {error}")
            return internal_error_response(f"Failed to create metadata entry: {error}")
        
        logger.info(f"Generated presigned URL for image: {image_id}")
        
        # Return presigned URL and image_id
        return success_response(
            data={
                'image_id': image_id,
                'upload_url': presigned_url,  # Changed from 'presigned_url' to match test expectations
                's3_key': s3_key,
                'expiry_seconds': expiry,
                'upload_method': 'PUT',
                'metadata': {
                    'image_id': image_id,
                    'filename': filename,
                    'content_type': content_type,
                    'user_id': user_id,
                    'status': 'processing',
                    'tags': tags,
                    'description': description
                },
                'headers': {
                    'Content-Type': content_type
                },
                'instructions': {
                    'step1': f'PUT {presigned_url}',
                    'step2': 'Set Content-Type header to: ' + content_type,
                    'step3': 'Upload image as binary body',
                    'step4': 'PATCH /images/{image_id} with status=active to mark as complete',
                    'note': 'Image status is "processing" until you mark it complete'
                }
            },
            message="Upload URL generated successfully",
            status_code=201
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in upload handler: {str(e)}", exc_info=True)
        return internal_error_response(str(e))
