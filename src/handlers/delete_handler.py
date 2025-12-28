"""
Lambda handler for deleting images.
Supports both soft delete (mark as deleted) and hard delete (remove from S3 and DynamoDB).
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
    Lambda handler for deleting images.
    
    Default behavior is soft delete (marks as deleted in DynamoDB).
    Set query parameter 'hard_delete=true' for permanent deletion.
    
    Path parameters:
    - image_id: Image ID (UUID)
    
    Headers:
    - user-id: User ID for authorization
    
    Query parameters:
    - hard_delete: If 'true', permanently delete from S3 and DynamoDB (default: false)
    
    Args:
        event: Lambda event
        context: Lambda context
    
    Returns:
        API Gateway response
    """
    try:
        logger.info("Delete handler invoked")
        
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
        
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        hard_delete = query_params.get('hard_delete', '').lower() == 'true'
        
        # Delete image
        image_service = ImageService()
        success, error = image_service.delete_image(
            image_id=image_id,
            user_id=user_id,
            soft_delete=not hard_delete
        )
        
        if not success:
            if error == "Image not found":
                return not_found_response("Image not found")
            elif error == "Unauthorized access":
                return error_response("Unauthorized access to this image", status_code=403)
            else:
                return internal_error_response(error)
        
        # Return success response
        delete_type = "permanently deleted" if hard_delete else "marked as deleted"
        
        return success_response(
            data={
                'image_id': image_id,
                'deleted': True,
                'delete_type': 'hard' if hard_delete else 'soft'
            },
            message=f"Image {delete_type} successfully"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in delete handler: {str(e)}", exc_info=True)
        return internal_error_response(str(e))
