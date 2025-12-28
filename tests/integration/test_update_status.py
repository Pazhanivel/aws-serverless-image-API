"""
Integration tests for update status endpoint.
"""

import pytest
import requests


class TestUpdateStatusEndpoint:
    """Test cases for PATCH /images/{image_id} endpoint."""
    
    @pytest.fixture
    def created_image_with_upload(
        self, api_base_url, api_headers, sample_image_metadata,
        sample_image_file, s3_client
    ):
        """Create a test image and upload file to S3."""
        # Create image metadata and get presigned URL
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=sample_image_metadata
        )
        assert response.status_code == 201
        response_data = response.json()
        data = response_data.get('data', response_data)  # Handle both wrapped and unwrapped responses
        
        # Upload file to S3
        upload_response = requests.put(
            data['upload_url'],
            data=sample_image_file,
            headers={'Content-Type': sample_image_metadata['content_type']}
        )
        assert upload_response.status_code in [200, 204]
        
        return data
    
    def test_update_status_to_active(
        self, api_base_url, api_headers, created_image_with_upload, 
        dynamodb_resource, cleanup
    ):
        """Test updating image status to active after upload."""
        image_id = created_image_with_upload['image_id']
        
        # Update status to active
        response = requests.patch(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers,
            json={
                'status': 'active',
                'size': len(created_image_with_upload.get('metadata', {}).get('content', b'test'))
            }
        )
        
        assert response.status_code == 200
        response_data = response.json()
        data = response_data.get('data', response_data)  # Unwrap success_response
        
        assert data['image_id'] == image_id
        assert data['status'] == 'active'
        assert 'message' in data
        
        # Verify in DynamoDB
        table = dynamodb_resource.Table('images')
        item = table.get_item(Key={'image_id': image_id})
        
        assert 'Item' in item
        assert item['Item']['status'] == 'active'
    
    def test_update_status_with_dimensions(
        self, api_base_url, api_headers, created_image_with_upload, cleanup
    ):
        """Test updating status with width and height."""
        image_id = created_image_with_upload['image_id']
        
        response = requests.patch(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers,
            json={
                'status': 'active',
                'size': 12345,
                'width': 1920,
                'height': 1080
            }
        )
        
        assert response.status_code == 200
        response_data = response.json()
        data = response_data.get('data', response_data)  # Unwrap success_response
        
        assert data['status'] == 'active'
        assert data['width'] == 1920
        assert data['height'] == 1080
    
    def test_update_status_nonexistent_image(self, api_base_url, api_headers):
        """Test updating status of non-existent image."""
        fake_id = 'non-existent-image-id-123'
        
        response = requests.patch(
            f"{api_base_url}/images/{fake_id}",
            headers=api_headers,
            json={'status': 'active'}
        )
        
        assert response.status_code == 404
    
    def test_update_status_wrong_user(
        self, api_base_url, api_headers, created_image_with_upload, cleanup
    ):
        """Test updating status of image belonging to different user."""
        image_id = created_image_with_upload['image_id']
        
        # Try to update with different user
        wrong_user_headers = api_headers.copy()
        wrong_user_headers['User-Id'] = 'different-user-999'
        
        response = requests.patch(
            f"{api_base_url}/images/{image_id}",
            headers=wrong_user_headers,
            json={'status': 'active'}
        )
        
        # Should return 404 or 403
        assert response.status_code in [403, 404]
    
    def test_update_status_missing_status_field(
        self, api_base_url, api_headers, created_image_with_upload, cleanup
    ):
        """Test updating without status field."""
        image_id = created_image_with_upload['image_id']
        
        response = requests.patch(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers,
            json={'size': 12345}
        )
        
        assert response.status_code in [400, 422]
    
    def test_update_status_invalid_status(
        self, api_base_url, api_headers, created_image_with_upload, cleanup
    ):
        """Test updating with invalid status value."""
        image_id = created_image_with_upload['image_id']
        
        response = requests.patch(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers,
            json={'status': 'invalid_status'}
        )
        
        assert response.status_code in [400, 422]
    
    def test_update_status_missing_user_id(
        self, api_base_url, created_image_with_upload, cleanup
    ):
        """Test updating without user-id header."""
        image_id = created_image_with_upload['image_id']
        
        response = requests.patch(
            f"{api_base_url}/images/{image_id}",
            headers={'Content-Type': 'application/json'},
            json={'status': 'active'}
        )
        
        assert response.status_code in [400, 422]
    
    def test_update_status_to_error(
        self, api_base_url, api_headers, created_image_with_upload, cleanup
    ):
        """Test updating status to error state."""
        image_id = created_image_with_upload['image_id']
        
        response = requests.patch(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers,
            json={'status': 'error'}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        data = response_data.get('data', response_data)  # Unwrap success_response
        
        assert data['status'] == 'error'
    
    def test_update_deleted_image_status(
        self, api_base_url, api_headers, created_image_with_upload, cleanup
    ):
        """Test updating status of deleted image."""
        image_id = created_image_with_upload['image_id']
        
        # Delete the image first
        delete_response = requests.delete(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        assert delete_response.status_code in [200, 204]  # Accept both 200 and 204
        
        # Try to update status
        response = requests.patch(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers,
            json={'status': 'active'}
        )
        
        # Should return 409 (conflict) or 400
        assert response.status_code in [400, 409]
    
    def test_update_status_invalid_size(
        self, api_base_url, api_headers, created_image_with_upload, cleanup
    ):
        """Test updating with invalid size value."""
        image_id = created_image_with_upload['image_id']
        
        response = requests.patch(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers,
            json={
                'status': 'active',
                'size': -100
            }
        )
        
        assert response.status_code in [400, 422]
    
    def test_update_status_invalid_dimensions(
        self, api_base_url, api_headers, created_image_with_upload, cleanup
    ):
        """Test updating with invalid width/height values."""
        image_id = created_image_with_upload['image_id']
        
        # Test negative width
        response = requests.patch(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers,
            json={
                'status': 'active',
                'width': -1920,
                'height': 1080
            }
        )
        
        assert response.status_code in [400, 422]
