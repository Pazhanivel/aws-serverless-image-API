"""
Lambda handler for updating image status.
Allows updating image status after successful S3 upload.

Typical flow:
1. Client requests presigned URL via POST /images
2. Client uploads to S3 using presigned URL
3. Client calls PATCH /images/{image_id} to mark as 'active'
"""

import json
import base64
from typing import Dict, Any
from datetime import datetime

from src.models.image_metadata import ImageMetadata
from src.services.dynamodb_service import DynamoDBService
from src.services.s3_service import S3Service
from src.utils.response import success_response, error_response, validation_error_response, not_found_response, internal_error_response
from src.utils.logger import get_logger
from src.utils.validators import validate_user_id


logger = get_logger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for updating image status.
    
    Path parameters:
    - image_id: Image ID
    
    Request body (JSON):
    {
        "status": "active",           // Required: 'active', 'processing', 'error'
        "size": 12345,                // Optional: file size in bytes
        "width": 1920,                // Optional: image width
        "height": 1080                // Optional: image height
    }
    
    Headers:
    - user-id: User ID (required)
    
    Response:
    {
        "success": true,
        "data": {
            "image_id": "uuid",
            "status": "active",
            "message": "Image status updated successfully"
        }
    }
    
    Args:
        event: Lambda event
        context: Lambda context
    
    Returns:
        API Gateway response
    """
    try:
        logger.info("Update status handler invoked")
        
        # Extract headers
        headers = event.get('headers', {}) or {}
        user_id = headers.get('user-id') or headers.get('User-Id', '')
        
        # Validate user_id
        if not user_id:
            return validation_error_response("user-id header is required")
        
        is_valid, error = validate_user_id(user_id)
        if not is_valid:
            return validation_error_response(f"Invalid user-id: {error}")
        
        # Extract path parameters
        path_params = event.get('pathParameters', {}) or {}
        image_id = path_params.get('image_id', '')
        
        if not image_id:
            return validation_error_response("image_id is required")
        
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
        
        # Validate required fields
        if 'status' not in data:
            return validation_error_response("Missing 'status' field")
        
        new_status = data['status']
        valid_statuses = ['active', 'processing', 'error']
        
        if new_status not in valid_statuses:
            return validation_error_response(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Extract optional fields
        size = data.get('size')
        width = data.get('width')
        height = data.get('height')
        
        # Validate optional numeric fields
        if size is not None:
            try:
                size = int(size)
                if size <= 0:
                    return validation_error_response("size must be greater than 0")
            except (ValueError, TypeError):
                return validation_error_response("size must be a valid integer")
        
        if width is not None:
            try:
                width = int(width)
                if width <= 0:
                    return validation_error_response("width must be greater than 0")
            except (ValueError, TypeError):
                return validation_error_response("width must be a valid integer")
        
        if height is not None:
            try:
                height = int(height)
                if height <= 0:
                    return validation_error_response("height must be greater than 0")
            except (ValueError, TypeError):
                return validation_error_response("height must be a valid integer")
        
        # Get existing metadata
        dynamodb_service = DynamoDBService()
        success, metadata, error_msg = dynamodb_service.get_metadata(image_id)
        
        if not success:
            logger.error(f"Failed to retrieve metadata: {error_msg}")
            return internal_error_response(f"Failed to retrieve image metadata: {error_msg}")
        
        if metadata is None:
            return not_found_response(f"Image not found: {image_id}")
        
        # Verify ownership
        if metadata.user_id != user_id:
            logger.warning(f"User {user_id} attempted to access image {image_id} owned by {metadata.user_id}")
            return not_found_response(f"Image not found: {image_id}")
        
        # Check if image is already deleted
        if metadata.status == 'deleted':
            return error_response("Cannot update status of deleted image", status_code=409)
        
        # Prepare update data
        update_data = {
            'status': new_status,
            'metadata': metadata.metadata or {}
        }
        
        # Add timestamp for status update
        update_data['metadata']['status_updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Update size if provided and status is active
        if size is not None and new_status == 'active':
            update_data['size'] = size
        
        # Update dimensions if provided
        if width is not None:
            update_data['width'] = width
        
        if height is not None:
            update_data['height'] = height
        
        # If status is being set to active and we have size, verify S3 object exists
        if new_status == 'active' and size is not None:
            try:
                s3_service = S3Service()
                exists, s3_size, error = s3_service.check_object_exists(
                    metadata.s3_bucket,
                    metadata.s3_key
                )
                
                if not exists:
                    logger.warning(f"S3 object not found for image {image_id}: {metadata.s3_key}")
                    return error_response(
                        "Cannot set status to active: file not found in S3. Please upload the file first.",
                        status_code=400
                    )
                
                # Use S3 size if size wasn't provided
                if s3_size and not size:
                    update_data['size'] = s3_size
                    
            except Exception as e:
                logger.error(f"Failed to verify S3 object: {str(e)}")
                # Continue anyway - S3 check is optional
        
        # Update metadata in DynamoDB
        success, error_msg = dynamodb_service.update_metadata(image_id, update_data)
        
        if not success:
            logger.error(f"Failed to update metadata: {error_msg}")
            return internal_error_response(f"Failed to update image status: {error_msg}")
        
        logger.info(f"Successfully updated status for image: {image_id} to {new_status}")
        
        # Return success response
        response_data = {
            'image_id': image_id,
            'status': new_status,
            'message': 'Image status updated successfully'
        }
        
        if size is not None:
            response_data['size'] = size
        if width is not None:
            response_data['width'] = width
        if height is not None:
            response_data['height'] = height
        
        return success_response(data=response_data)
        
    except Exception as e:
        logger.error(f"Unexpected error in update status handler: {str(e)}", exc_info=True)
        return internal_error_response(str(e))
