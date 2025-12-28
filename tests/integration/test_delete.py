"""
Integration tests for delete endpoint.
"""

import pytest
import requests
import time


class TestDeleteEndpoint:
    """Test cases for DELETE /images/{image_id} endpoint."""
    
    @pytest.fixture
    def created_image(self, api_base_url, api_headers, sample_image_metadata):
        """Create a test image for deletion testing."""
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=sample_image_metadata
        )
        assert response.status_code == 201
        return response.json()
    
    @pytest.fixture
    def created_image_with_file(
        self, api_base_url, api_headers, sample_image_metadata, 
        sample_image_file, s3_client
    ):
        """Create image with file uploaded to S3."""
        # Create metadata and get presigned URL
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=sample_image_metadata
        )
        response_data = response.json()
        data = response_data['data']
        
        # Upload file to S3
        upload_response = requests.put(
            data['upload_url'],
            data=sample_image_file,
            headers={'Content-Type': sample_image_metadata['content_type']}
        )
        assert upload_response.status_code in [200, 204]
        
        return response_data
    
    def test_delete_soft_delete_success(
        self, api_base_url, api_headers, created_image, dynamodb_resource
    ):
        """Test successful soft delete (default behavior)."""
        image_id = created_image['data']['image_id']
        
        response = requests.delete(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'deleted' in data['message'].lower()
        
        # Verify image still exists in DynamoDB but marked as deleted
        table = dynamodb_resource.Table('images')
        item = table.get_item(Key={'image_id': image_id})
        
        assert 'Item' in item
        assert item['Item']['status'] == 'deleted'
    
    def test_delete_hard_delete_success(
        self, api_base_url, api_headers, created_image_with_file, 
        dynamodb_resource, s3_client
    ):
        """Test successful hard delete."""
        image_id = created_image_with_file['data']['image_id']
        
        response = requests.delete(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers,
            params={'hard_delete': 'true'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        
        # Verify image removed from DynamoDB
        table = dynamodb_resource.Table('images')
        item = table.get_item(Key={'image_id': image_id})
        assert 'Item' not in item
        
        # Verify file removed from S3
        try:
            s3_client.head_object(Bucket='image-storage-bucket', Key=image_id)
            pytest.fail("S3 object should have been deleted")
        except s3_client.exceptions.ClientError as e:
            assert e.response['Error']['Code'] == '404'
    
    def test_delete_nonexistent_image(self, api_base_url, api_headers):
        """Test deleting non-existent image."""
        fake_id = 'non-existent-image-id-123'
        
        response = requests.delete(
            f"{api_base_url}/images/{fake_id}",
            headers=api_headers
        )
        
        assert response.status_code in [404, 422]
        data = response.json()
        assert data['success'] is False
    
    def test_delete_wrong_user(
        self, api_base_url, api_headers, created_image
    ):
        """Test deleting image belonging to different user."""
        image_id = created_image['data']['image_id']
        
        # Try to delete with different user
        wrong_user_headers = api_headers.copy()
        wrong_user_headers['User-Id'] = 'different-user-999'
        
        response = requests.delete(
            f"{api_base_url}/images/{image_id}",
            headers=wrong_user_headers
        )
        
        # Should return 404 or 403
        assert response.status_code in [403, 404]
        
        # Verify image still exists
        get_response = requests.get(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        assert get_response.status_code == 200
    
    def test_delete_missing_user_id(
        self, api_base_url, created_image
    ):
        """Test deleting without user-id header."""
        image_id = created_image['data']['image_id']
        
        response = requests.delete(
            f"{api_base_url}/images/{image_id}",
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert data['success'] is False
    
    def test_delete_already_deleted_image(
        self, api_base_url, api_headers, created_image
    ):
        """Test deleting an already deleted image."""
        image_id = created_image['data']['image_id']
        
        # First delete (soft)
        response1 = requests.delete(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        assert response1.status_code == 200
        
        # Try to delete again
        response2 = requests.delete(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        
        # Should return 404 or success (idempotent)
        assert response2.status_code in [200, 404]
    
    def test_delete_invalid_image_id(self, api_base_url, api_headers):
        """Test delete with invalid image ID format."""
        invalid_ids = ['', '   ', '../../../etc/passwd']
        
        for invalid_id in invalid_ids:
            response = requests.delete(
                f"{api_base_url}/images/{invalid_id}",
                headers=api_headers
            )
            
            assert response.status_code in [200, 400, 403, 404, 422]
    
    def test_soft_delete_then_hard_delete(
        self, api_base_url, api_headers, created_image_with_file, 
        dynamodb_resource, s3_client
    ):
        """Test soft delete followed by hard delete."""
        image_id = created_image_with_file['data']['image_id']
        
        # Soft delete first
        response1 = requests.delete(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        assert response1.status_code == 200
        
        time.sleep(0.5)  # Small delay
        
        # Then hard delete
        response2 = requests.delete(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers,
            params={'hard_delete': 'true'}
        )
        
        # Should succeed or return not found
        assert response2.status_code in [200, 404]
        
        # Verify completely removed
        table = dynamodb_resource.Table('images')
        item = table.get_item(Key={'image_id': image_id})
        assert 'Item' not in item
    
    def test_delete_metadata_without_file(
        self, api_base_url, api_headers, created_image, dynamodb_resource, s3_client
    ):
        """Test hard deleting image that has no S3 file."""
        image_id = created_image['data']['image_id']
        
        # Hard delete (no file uploaded yet)
        response = requests.delete(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers,
            params={'hard_delete': 'true'}
        )
        
        # Should still succeed
        assert response.status_code == 200
        
        # Verify removed from DynamoDB
        table = dynamodb_resource.Table('images')
        item = table.get_item(Key={'image_id': image_id})
        assert 'Item' not in item
    
    def test_delete_and_verify_not_in_list(
        self, api_base_url, api_headers, created_image
    ):
        """Test that soft-deleted images don't appear in list."""
        image_id = created_image['data']['image_id']
        
        # Soft delete
        delete_response = requests.delete(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        assert delete_response.status_code == 200
        
        # List images
        list_response = requests.get(
            f"{api_base_url}/images",
            headers=api_headers
        )
        
        assert list_response.status_code == 200
        images = list_response.json()['data']['items']
        
        # Deleted image should not appear (or have status='deleted')
        for image in images:
            if image['image_id'] == image_id:
                assert image['status'] == 'deleted'
