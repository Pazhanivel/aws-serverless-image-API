"""
Response formatter utility for standardized API responses.
Provides consistent response structure across all Lambda handlers.
"""

from typing import Any, Dict, Optional, List, Union
import json
from datetime import datetime


def success_response(
    data: Any,
    message: str = "Success",
    status_code: int = 200
) -> Dict[str, Any]:
    """
    Create a successful API response.
    
    Args:
        data: Response data (dict, list, or any JSON-serializable object)
        message: Success message
        status_code: HTTP status code (default: 200)
    
    Returns:
        Formatted API Gateway response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps({
            'success': True,
            'message': message,
            'data': data,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    }


def error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create an error API response.
    
    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        error_code: Application-specific error code
        details: Additional error details
    
    Returns:
        Formatted API Gateway error response
    """
    body = {
        'success': False,
        'message': message,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    if error_code:
        body['error_code'] = error_code
    
    if details:
        body['details'] = details
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }


def validation_error_response(
    errors: Union[str, List[Dict[str, str]]]
) -> Dict[str, Any]:
    """
    Create a validation error response.
    
    Args:
        errors: List of validation errors with field and message
                Example: [{'field': 'email', 'message': 'Invalid email format'}]
    
    Returns:
        Formatted API Gateway validation error response
    """
    # Support both structured list of errors and a single message
    details: Dict[str, Any]
    if isinstance(errors, str):
        details = {'errors': [{'message': errors}]}
    else:
        details = {'errors': errors}

    return error_response(
        message='Validation failed',
        status_code=422,
        error_code='VALIDATION_ERROR',
        details=details
    )


def not_found_response(
    resource: str = "Resource"
) -> Dict[str, Any]:
    """
    Create a not found error response.
    
    Args:
        resource: Name of the resource that was not found
    
    Returns:
        Formatted API Gateway 404 response
    """
    return error_response(
        message=f'{resource} not found',
        status_code=404,
        error_code='NOT_FOUND'
    )


def internal_error_response(
    message: str = "Internal server error"
) -> Dict[str, Any]:
    """
    Create an internal server error response.
    
    Args:
        message: Error message
    
    Returns:
        Formatted API Gateway 500 response
    """
    return error_response(
        message=message,
        status_code=500,
        error_code='INTERNAL_ERROR'
    )


def paginated_response(
    items: List[Any],
    total_count: Optional[int] = None,
    next_token: Optional[str] = None,
    message: str = "Success"
) -> Dict[str, Any]:
    """
    Create a paginated success response.
    
    Args:
        items: List of items for current page
        total_count: Total number of items (optional)
        next_token: Token for next page (optional)
        message: Success message
    
    Returns:
        Formatted API Gateway response with pagination info
    """
    data = {
        'items': items,
        'count': len(items)
    }
    
    if total_count is not None:
        data['total_count'] = total_count
    
    if next_token:
        data['next_token'] = next_token
        data['has_more'] = True
    else:
        data['has_more'] = False
    
    return success_response(data=data, message=message)
