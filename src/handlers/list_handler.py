"""
Lambda handler for listing images with filters and pagination.
"""

import json
from typing import Dict, Any, Optional, List

from src.services.image_service import ImageService
from src.utils.response import success_response, validation_error_response, internal_error_response, paginated_response
from src.utils.logger import get_logger
from src.utils.validators import validate_user_id


logger = get_logger(__name__)


def parse_query_parameters(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and validate query parameters.
    
    Supported parameters:
    - user_id: str (required if not in header)
    - tags: str (comma-separated)
    - content_type: str
    - status: str (optional: 'active', 'processing', 'deleted'. Default: None (all statuses))
    - min_size: int
    - max_size: int
    - limit: int (default: 50, max: 100)
    - next_token: str (pagination token)
    
    Args:
        event: Lambda event
    
    Returns:
        Dictionary with parsed parameters
    """
    query_params = event.get('queryStringParameters') or {}
    headers = event.get('headers', {}) or {}
    
    # Get user_id from query params or header
    user_id = query_params.get('user_id') or headers.get('user-id') or headers.get('User-Id', '')
    
    # Parse tags
    tags = None
    if query_params.get('tags'):
        tags = [tag.strip() for tag in query_params['tags'].split(',') if tag.strip()]
    
    # Parse content_type
    content_type = query_params.get('content_type')
    
    # Parse status (None = all statuses, or specify 'active', 'processing', 'deleted')
    status = query_params.get('status')
    
    # Parse size filters
    min_size = None
    max_size = None
    
    if query_params.get('min_size'):
        try:
            min_size = int(query_params['min_size'])
        except ValueError:
            pass
    
    if query_params.get('max_size'):
        try:
            max_size = int(query_params['max_size'])
        except ValueError:
            pass
    
    # Parse limit
    limit = 50
    if query_params.get('limit'):
        try:
            limit = int(query_params['limit'])
            # Cap at 100
            limit = min(limit, 100)
        except ValueError:
            pass
    
    # Parse pagination token
    next_token = query_params.get('next_token')
    last_evaluated_key = None
    
    if next_token:
        try:
            import base64
            decoded = base64.b64decode(next_token).decode('utf-8')
            last_evaluated_key = json.loads(decoded)
        except Exception as e:
            logger.warning(f"Invalid pagination token: {str(e)}")
    
    return {
        'user_id': user_id,
        'tags': tags,
        'content_type': content_type,
        'status': status,
        'min_size': min_size,
        'max_size': max_size,
        'limit': limit,
        'last_evaluated_key': last_evaluated_key
    }


def encode_pagination_token(last_evaluated_key: Dict[str, Any]) -> str:
    """
    Encode pagination token.
    
    Args:
        last_evaluated_key: DynamoDB LastEvaluatedKey
    
    Returns:
        Base64-encoded token
    """
    import base64
    
    token_json = json.dumps(last_evaluated_key)
    token_bytes = token_json.encode('utf-8')
    return base64.b64encode(token_bytes).decode('utf-8')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for listing images.
    
    Query parameters:
    - user_id: Filter by user (optional if in header)
    - tags: Comma-separated tags
    - content_type: Filter by MIME type
    - status: Filter by status (optional: 'active', 'processing', 'deleted'. Default: all statuses)
    - min_size: Minimum file size
    - max_size: Maximum file size
    - limit: Results per page (default: 50, max: 100)
    - next_token: Pagination token
    
    Args:
        event: Lambda event
        context: Lambda context
    
    Returns:
        API Gateway response with image list
    """
    try:
        logger.info("List handler invoked")
        
        # Parse parameters
        params = parse_query_parameters(event)
        
        user_id = params['user_id']
        
        # Validate user_id
        if not user_id:
            return validation_error_response("user_id parameter or user-id header is required")
        
        is_valid, error = validate_user_id(user_id)
        if not is_valid:
            return validation_error_response(f"Invalid user_id: {error}")
        
        # Determine if we need advanced filtering
        use_advanced_filters = any([
            params['tags'],
            params['content_type'],
            params['min_size'],
            params['max_size']
        ])
        
        # Query images
        image_service = ImageService()
        
        if use_advanced_filters:
            # Use search with filters
            success, metadata_list, next_key, error = image_service.search_images(
                user_id=user_id,
                tags=params['tags'],
                content_type=params['content_type'],
                status=params['status'],
                min_size=params['min_size'],
                max_size=params['max_size'],
                limit=params['limit'],
                last_evaluated_key=params['last_evaluated_key']
            )
        else:
            # Simple list by user
            success, metadata_list, next_key, error = image_service.list_user_images(
                user_id=user_id,
                status=params['status'],
                limit=params['limit'],
                last_evaluated_key=params['last_evaluated_key']
            )
        
        if not success:
            return internal_error_response(error)
        
        # Convert metadata to dict
        images = []
        for metadata in metadata_list:
            images.append({
                'image_id': metadata.image_id,
                'user_id': metadata.user_id,
                'filename': metadata.filename,
                'content_type': metadata.content_type,
                'size': metadata.size,
                'upload_timestamp': metadata.upload_timestamp,
                'tags': metadata.tags,
                'description': metadata.description,
                'width': metadata.width,
                'height': metadata.height,
                'status': metadata.status
            })
        
        # Encode pagination token
        next_token = None
        if next_key:
            next_token = encode_pagination_token(next_key)
        
        # Return paginated response
        return paginated_response(
            items=images,
            next_token=next_token,
            total_count=len(images)
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in list handler: {str(e)}", exc_info=True)
        return internal_error_response(str(e))
