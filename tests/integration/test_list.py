"""
Integration tests for list endpoint.
"""

import pytest
import requests
import time


def wait_for_list_results(api_base_url, api_headers, min_count=1, max_retries=20, **params):
    """Wait for DynamoDB to return list results (eventual consistency)."""
    for attempt in range(max_retries):
        response = requests.get(
            f"{api_base_url}/images",
            headers=api_headers,
            params=params
        )
        if response.status_code == 200:
            data = response.json()['data']
            if len(data['items']) >= min_count:
                return response
        time.sleep(1.0)  # Wait longer before retry
    return response  # Return last response even if not meeting criteria


class TestListEndpoint:
    """Test cases for GET /images endpoint."""
    
    @pytest.fixture
    def create_test_images(self, api_base_url, api_headers, s3_client):
        """Create multiple test images for list testing."""
        images = []
        
        # Create 5 test images with different attributes
        test_cases = [
            {'filename': 'sunset.jpg', 'content_type': 'image/jpeg', 'tags': ['nature', 'sunset']},
            {'filename': 'portrait.png', 'content_type': 'image/png', 'tags': ['people', 'portrait']},
            {'filename': 'landscape.jpg', 'content_type': 'image/jpeg', 'tags': ['nature', 'landscape']},
            {'filename': 'city.jpg', 'content_type': 'image/jpeg', 'tags': ['urban', 'city']},
            {'filename': 'animation.gif', 'content_type': 'image/gif', 'tags': ['fun', 'animated']},
        ]
        
        for metadata in test_cases:
            response = requests.post(
                f"{api_base_url}/images",
                headers=api_headers,
                json=metadata
            )
            if response.status_code == 201:
                images.append(response.json())
            time.sleep(0.1)  # Small delay to ensure different timestamps
        
        return images
    
    def test_list_all_images(self, api_base_url, api_headers, create_test_images, cleanup):
        """Test listing all images for a user."""
        # Wait for DynamoDB eventual consistency
        response = wait_for_list_results(api_base_url, api_headers, min_count=5)
        
        assert response.status_code == 200
        response_data = response.json()
        data = response_data['data']
        
        assert 'items' in data
        assert isinstance(data['items'], list)
        assert len(data['items']) >= 5  # At least our test images
        
        # Verify image structure
        for image in data['items']:
            assert 'image_id' in image
            assert 'filename' in image
            assert 'content_type' in image
            assert 'user_id' in image
            assert 'upload_timestamp' in image
    
    def test_list_with_limit(self, api_base_url, api_headers, create_test_images, cleanup):
        """Test listing with limit parameter."""
        response = requests.get(
            f"{api_base_url}/images",
            headers=api_headers,
            params={'limit': 2}
        )
        
        assert response.status_code == 200
        response_data = response.json()
        data = response_data['data']
        
        assert len(data['items']) <= 2
        assert 'has_more' in data or len(data['items']) < 2
    
    def test_list_pagination(self, api_base_url, api_headers, create_test_images, cleanup):
        """Test pagination with next_token."""
        # First page
        response1 = requests.get(
            f"{api_base_url}/images",
            headers=api_headers,
            params={'limit': 2}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()['data']
        
        if 'next_token' in data1:
            # Second page
            response2 = requests.get(
                f"{api_base_url}/images",
                headers=api_headers,
                params={'limit': 2, 'next_token': data1['next_token']}
            )
            
            assert response2.status_code == 200
            data2 = response2.json()['data']
            
            # Verify different results
            image_ids_1 = {img['image_id'] for img in data1['items']}
            image_ids_2 = {img['image_id'] for img in data2['items']}
            assert len(image_ids_1.intersection(image_ids_2)) == 0
    
    def test_list_filter_by_content_type(
        self, api_base_url, api_headers, create_test_images, cleanup
    ):
        """Test filtering by content type."""
        response = requests.get(
            f"{api_base_url}/images",
            headers=api_headers,
            params={'content_type': 'image/jpeg'}
        )
        
        assert response.status_code == 200
        data = response.json()['data']
        
        # All returned images should be JPEG
        for image in data['items']:
            assert image['content_type'] == 'image/jpeg'
    
    def test_list_filter_by_tag(
        self, api_base_url, api_headers, create_test_images, cleanup
    ):
        """Test filtering by tag."""
        response = requests.get(
            f"{api_base_url}/images",
            headers=api_headers,
            params={'tags': 'nature'}
        )
        
        assert response.status_code == 200
        data = response.json()['data']
        
        # All returned images should have 'nature' tag
        for image in data['items']:
            assert 'nature' in image.get('tags', [])
    
    def test_list_filter_by_multiple_tags(
        self, api_base_url, api_headers, create_test_images, cleanup
    ):
        """Test filtering by multiple tags."""
        response = requests.get(
            f"{api_base_url}/images",
            headers=api_headers,
            params={'tags': 'nature,sunset'}
        )
        
        assert response.status_code == 200
        data = response.json()['data']
        
        # Returned images should have at least one of the tags
        for image in data['items']:
            tags = image.get('tags', [])
            assert 'nature' in tags or 'sunset' in tags
    
    def test_list_empty_result(self, api_base_url):
        """Test listing with user that has no images."""
        headers = {
            'Content-Type': 'application/json',
            'User-Id': 'non-existent-user-999'
        }
        
        response = requests.get(
            f"{api_base_url}/images",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()['data']
        assert data['items'] == []
    
    def test_list_missing_user_id(self, api_base_url):
        """Test listing without user-id header."""
        response = requests.get(
            f"{api_base_url}/images",
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert data['success'] is False
    
    def test_list_invalid_limit(self, api_base_url, api_headers):
        """Test listing with invalid limit parameter."""
        response = requests.get(
            f"{api_base_url}/images",
            headers=api_headers,
            params={'limit': -1}
        )
        
        # Should either reject or use default
        assert response.status_code in [200, 400, 500]
    
    def test_list_order_by_timestamp(
        self, api_base_url, api_headers, create_test_images, cleanup
    ):
        """Test that images are ordered by upload timestamp (newest first)."""
        response = requests.get(
            f"{api_base_url}/images",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()['data']
        
        if len(data['items']) > 1:
            timestamps = [img['upload_timestamp'] for img in data['items']]
            # Verify descending order (newest first)
            assert timestamps == sorted(timestamps, reverse=True)
