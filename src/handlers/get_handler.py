"""
Lambda handler for retrieving image metadata.
"""

import json
from typing import Dict, Any

from src.services.image_service import ImageService
from src.utils.response import success_response, not_found_response, validation_error_response, internal_error_response, error_response
from src.utils.logger import get_logger
from src.utils.validators import validate_image_id, validate_user_id


logger = get_logger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for retrieving image metadata.
    
    Path parameters:
    - image_id: Image ID (UUID)
    
    Headers:
    - user-id: User ID for authorization
    
    Args:
        event: Lambda event
        context: Lambda context
    
    Returns:
        API Gateway response with image metadata
    """
    try:
        logger.info("Get handler invoked")
        
        # Extract image_id from path parameters
        path_params = event.get('pathParameters') or {}
        image_id = path_params.get('image_id', '')
        
        if not image_id:
            return validation_error_response("image_id path parameter is required")
        
        # Validate image_id format
        is_valid, error = validate_image_id(image_id)
        if not is_valid:
            return validation_error_response(f"Invalid image_id: {error}")
        
        # Extract user_id from headers
        headers = event.get('headers', {}) or {}
        user_id = headers.get('user-id') or headers.get('User-Id', '')
        
        if not user_id:
            return validation_error_response("user-id header is required")
        
        # Validate user_id
        is_valid, error = validate_user_id(user_id)
        if not is_valid:
            return validation_error_response(f"Invalid user_id: {error}")
        
        # Get image metadata
        image_service = ImageService()
        success, metadata, error = image_service.get_image_metadata(
            image_id=image_id,
            user_id=user_id
        )
        
        if not success:
            if error == "Image not found":
                return not_found_response("Image not found")
            elif error == "Unauthorized access":
                return error_response("Unauthorized access to this image", status_code=403)
            else:
                return internal_error_response(error)
        
        # Return metadata
        return success_response(
            data={
                'image_id': metadata.image_id,
                'user_id': metadata.user_id,
                'filename': metadata.filename,
                'content_type': metadata.content_type,
                'size': metadata.size,
                's3_key': metadata.s3_key,
                's3_bucket': metadata.s3_bucket,
                'upload_timestamp': metadata.upload_timestamp,
                'tags': metadata.tags,
                'description': metadata.description,
                'width': metadata.width,
                'height': metadata.height,
                'status': metadata.status,
                'metadata': metadata.metadata
            },
            message="Image metadata retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in get handler: {str(e)}", exc_info=True)
        return internal_error_response(str(e))
