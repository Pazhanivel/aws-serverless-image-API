"""
Lambda handler for downloading images.
Generates presigned S3 URLs for secure downloads.
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
    Lambda handler for downloading images.
    
    Returns a presigned S3 URL for downloading the image.
    
    Path parameters:
    - image_id: Image ID (UUID)
    
    Headers:
    - user-id: User ID for authorization
    
    Query parameters:
    - expiry: URL expiry in seconds (default: 900, i.e., 15 minutes)
    - redirect: If 'true', returns 302 redirect instead of JSON
    
    Args:
        event: Lambda event
        context: Lambda context
    
    Returns:
        API Gateway response with presigned URL or redirect
    """
    try:
        logger.info("Download handler invoked")
        
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
        
        # Parse expiry
        expiry = 900  # Default 15 minutes
        if query_params.get('expiry'):
            try:
                expiry = int(query_params['expiry'])
                # Cap at 1 hour
                expiry = min(expiry, 3600)
            except ValueError:
                return validation_error_response("Invalid expiry value. Must be an integer.")
        
        # Check if redirect is requested
        redirect = query_params.get('redirect', '').lower() == 'true'
        
        # Generate presigned URL
        image_service = ImageService()
        success, presigned_url, error = image_service.generate_presigned_url(
            image_id=image_id,
            user_id=user_id,
            expiry=expiry
        )
        
        if not success:
            if error == "Image not found":
                return not_found_response("Image not found")
            elif error == "Unauthorized access":
                return error_response("Unauthorized access to this image", status_code=403)
            elif error == "Image has been deleted":
                return error_response("Image has been deleted", status_code=410)
            else:
                return internal_error_response(error)
        
        # Return response
        if redirect:
            # Return 302 redirect
            return {
                'statusCode': 302,
                'headers': {
                    'Location': presigned_url,
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization, user-id'
                },
                'body': ''
            }
        else:
            # Return JSON with presigned URL
            return success_response(
                data={
                    'presigned_url': presigned_url,
                    'image_id': image_id,
                    'expiry_seconds': expiry,
                    'expires_at': None  # Could calculate ISO timestamp
                },
                message="Presigned download URL generated successfully"
            )
        
    except Exception as e:
        logger.error(f"Unexpected error in download handler: {str(e)}", exc_info=True)
        return internal_error_response(str(e))
