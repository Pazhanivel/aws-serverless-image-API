"""
Integration tests for get metadata endpoint.
"""

import pytest
import requests


class TestGetEndpoint:
    """Test cases for GET /images/{image_id} endpoint."""
    
    @pytest.fixture
    def created_image(self, api_base_url, api_headers, sample_image_metadata):
        """Create a test image and return its ID."""
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=sample_image_metadata
        )
        assert response.status_code == 201
        return response.json()
    
    def test_get_image_metadata_success(
        self, api_base_url, api_headers, created_image, cleanup
    ):
        """Test successfully retrieving image metadata."""
        image_id = created_image['data']['image_id']
        
        response = requests.get(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        
        assert response.status_code == 200
        response_data = response.json()
        data = response_data['data']
        
        # Verify metadata structure
        assert data['image_id'] == image_id
        assert 'filename' in data
        assert 'content_type' in data
        assert data['user_id'] == api_headers['User-Id']
        assert 'upload_timestamp' in data
        assert 'status' in data
    
    def test_get_image_with_tags(
        self, api_base_url, api_headers, cleanup
    ):
        """Test retrieving image with tags."""
        # Create image with tags
        metadata = {
            'filename': 'tagged.jpg',
            'content_type': 'image/jpeg',
            'tags': ['test', 'integration', 'metadata']
        }
        
        create_response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=metadata
        )
        image_id = create_response.json()['data']['image_id']
        
        # Get metadata
        response = requests.get(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()['data']
        assert set(data['tags']) == set(metadata['tags'])
    
    def test_get_image_with_description(
        self, api_base_url, api_headers, cleanup
    ):
        """Test retrieving image with description."""
        metadata = {
            'filename': 'described.jpg',
            'content_type': 'image/jpeg',
            'description': 'This is a test description'
        }
        
        create_response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=metadata
        )
        image_id = create_response.json()['data']['image_id']
        
        response = requests.get(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()['data']
        assert data['description'] == metadata['description']
    
    def test_get_nonexistent_image(self, api_base_url, api_headers):
        """Test retrieving non-existent image."""
        fake_id = 'non-existent-image-id-123'
        
        response = requests.get(
            f"{api_base_url}/images/{fake_id}",
            headers=api_headers
        )
        
        assert response.status_code in [404, 422]
        data = response.json()
        assert data['success'] is False
        # Validation error or not found error
        assert data['message'] in ['Validation failed', 'Image not found']
    
    def test_get_image_wrong_user(
        self, api_base_url, api_headers, created_image, cleanup
    ):
        """Test retrieving image belonging to different user."""
        image_id = created_image['data']['image_id']
        
        # Try to access with different user
        wrong_user_headers = api_headers.copy()
        wrong_user_headers['User-Id'] = 'different-user-456'
        
        response = requests.get(
            f"{api_base_url}/images/{image_id}",
            headers=wrong_user_headers
        )
        
        # Should return 404 or 403
        assert response.status_code in [403, 404]
    
    def test_get_image_missing_user_id(
        self, api_base_url, created_image
    ):
        """Test retrieving image without user-id header."""
        image_id = created_image['data']['image_id']
        
        response = requests.get(
            f"{api_base_url}/images/{image_id}",
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert data['success'] is False
    
    def test_get_image_invalid_id_format(self, api_base_url, api_headers):
        """Test retrieving image with invalid ID format."""
        invalid_ids = ['', '   ', 'invalid id with spaces', '../../../etc/passwd']
        
        for invalid_id in invalid_ids:
            response = requests.get(
                f"{api_base_url}/images/{invalid_id}",
                headers=api_headers
            )
            
            # Should reject invalid IDs
            assert response.status_code in [200, 400, 404, 422]
    
    def test_get_image_metadata_completeness(
        self, api_base_url, api_headers, cleanup
    ):
        """Test that all metadata fields are returned."""
        # Create image with all possible fields
        metadata = {
            'filename': 'complete.jpg',
            'content_type': 'image/jpeg',
            'tags': ['complete', 'full', 'metadata'],
            'description': 'Complete metadata test',
            'size': 12345
        }
        
        create_response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=metadata
        )
        image_id = create_response.json()['data']['image_id']
        
        response = requests.get(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()['data']
        
        # Verify all expected fields are present
        required_fields = [
            'image_id', 'filename', 'content_type', 'user_id', 
            'upload_timestamp', 'status'
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify optional fields if provided
        assert 'tags' in data
        assert 'description' in data
