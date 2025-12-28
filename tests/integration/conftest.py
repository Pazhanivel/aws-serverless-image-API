"""
Base fixtures and utilities for integration tests.
"""

import os
import pytest
import boto3
import requests
from typing import Dict, Any, Optional

# Test configuration
LOCALSTACK_ENDPOINT = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'image-storage-bucket')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'images')


@pytest.fixture(scope='session')
def aws_credentials():
    """Mock AWS credentials for LocalStack."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'test'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
    os.environ['AWS_DEFAULT_REGION'] = AWS_REGION


@pytest.fixture(scope='session')
def s3_client(aws_credentials):
    """Create S3 client for LocalStack."""
    return boto3.client(
        's3',
        endpoint_url=LOCALSTACK_ENDPOINT,
        region_name=AWS_REGION
    )


@pytest.fixture(scope='session')
def dynamodb_client(aws_credentials):
    """Create DynamoDB client for LocalStack."""
    return boto3.client(
        'dynamodb',
        endpoint_url=LOCALSTACK_ENDPOINT,
        region_name=AWS_REGION
    )


@pytest.fixture(scope='session')
def dynamodb_resource(aws_credentials):
    """Create DynamoDB resource for LocalStack."""
    return boto3.resource(
        'dynamodb',
        endpoint_url=LOCALSTACK_ENDPOINT,
        region_name=AWS_REGION
    )


@pytest.fixture(scope='session')
def api_gateway_client(aws_credentials):
    """Create API Gateway client for LocalStack."""
    return boto3.client(
        'apigateway',
        endpoint_url=LOCALSTACK_ENDPOINT,
        region_name=AWS_REGION
    )


@pytest.fixture(scope='session')
def api_base_url(api_gateway_client) -> str:
    """Get the API Gateway base URL."""
    # Get the REST API ID
    response = api_gateway_client.get_rest_apis()
    apis = [api for api in response.get('items', []) if api['name'] == 'image-api']
    
    if not apis:
        pytest.skip("API Gateway not deployed. Run scripts/deploy_stack.py first.")
    
    # Get the most recent API (by creation date)
    api = sorted(apis, key=lambda x: x.get('createdDate', 0), reverse=True)[0]
    api_id = api['id']
    return f"{LOCALSTACK_ENDPOINT}/restapis/{api_id}/dev/_user_request_"


@pytest.fixture
def test_user_id() -> str:
    """Return a test user ID."""
    return "test-user-123"


@pytest.fixture
def api_headers(test_user_id) -> Dict[str, str]:
    """Return default API headers."""
    return {
        'Content-Type': 'application/json',
        'User-Id': test_user_id
    }


@pytest.fixture
def sample_image_metadata() -> Dict[str, Any]:
    """Return sample image metadata for testing."""
    return {
        'filename': 'test-image.jpg',
        'content_type': 'image/jpeg',
        'tags': ['test', 'sample'],
        'description': 'Test image for integration testing'
    }


@pytest.fixture
def sample_image_file() -> bytes:
    """Return sample image file content (1x1 red pixel JPEG)."""
    # Minimal valid JPEG file (1x1 red pixel)
    return (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c'
        b'\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c'
        b'\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00'
        b'\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\t\xff\xc4\x00\x14\x10\x01'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff'
        b'\xda\x00\x08\x01\x01\x00\x00?\x00T\xdf\xff\xd9'
    )


def cleanup_test_images(dynamodb_resource, s3_client, user_id: str):
    """Clean up test images from DynamoDB and S3."""
    table = dynamodb_resource.Table(DYNAMODB_TABLE_NAME)
    
    # Scan for test user's images
    response = table.query(
        IndexName='UserIndex',
        KeyConditionExpression='user_id = :uid',
        ExpressionAttributeValues={':uid': user_id}
    )
    
    # Delete from DynamoDB and S3
    for item in response.get('Items', []):
        image_id = item['image_id']
        
        # Delete from DynamoDB
        table.delete_item(Key={'image_id': image_id})
        
        # Delete from S3
        try:
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=image_id)
        except:
            pass


@pytest.fixture
def cleanup(dynamodb_resource, s3_client, test_user_id):
    """Fixture to clean up test data after each test."""
    yield
    cleanup_test_images(dynamodb_resource, s3_client, test_user_id)
