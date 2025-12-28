"""
Integration tests for download endpoint.
"""

import pytest
import requests


class TestDownloadEndpoint:
    """Test cases for GET /images/{image_id}/download endpoint."""
    
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
        data = response_data['data']
        
        # Upload file to S3
        upload_response = requests.put(
            data['upload_url'],
            data=sample_image_file,
            headers={'Content-Type': sample_image_metadata['content_type']}
        )
        assert upload_response.status_code in [200, 204]
        
        return response_data
    
    def test_download_get_presigned_url(
        self, api_base_url, api_headers, created_image_with_upload, cleanup
    ):
        """Test getting presigned download URL."""
        image_id = created_image_with_upload['data']['image_id']
        
        response = requests.get(
            f"{api_base_url}/images/{image_id}/download",
            headers=api_headers
        )
        
        assert response.status_code == 200
        response_data = response.json()
        data = response_data['data']
        
        assert 'presigned_url' in data
        assert 'image_id' in data
        assert data['image_id'] == image_id
        
        # Verify URL is valid
        assert data['presigned_url'].startswith('http')
        assert 'image-storage-bucket' in data['presigned_url']
    
    def test_download_with_redirect(
        self, api_base_url, api_headers, created_image_with_upload, cleanup
    ):
        """Test download with redirect parameter."""
        image_id = created_image_with_upload['data']['image_id']
        
        response = requests.get(
            f"{api_base_url}/images/{image_id}/download",
            headers=api_headers,
            params={'redirect': 'true'},
            allow_redirects=False
        )
        
        # Should return 302 redirect
        assert response.status_code == 302
        assert 'Location' in response.headers
        
        # Location should be presigned URL
        location = response.headers['Location']
        assert location.startswith('http')
        assert 'image-storage-bucket' in location
    
    def test_download_file_content(
        self, api_base_url, api_headers, created_image_with_upload, 
        sample_image_file, cleanup
    ):
        """Test downloading actual file content using presigned URL."""
        image_id = created_image_with_upload['data']['image_id']
        
        # Get presigned URL
        response = requests.get(
            f"{api_base_url}/images/{image_id}/download",
            headers=api_headers
        )
        
        assert response.status_code == 200
        download_url = response.json()['data']['presigned_url']
        
        # Download file using presigned URL
        file_response = requests.get(download_url)
        
        assert file_response.status_code == 200
        assert file_response.content == sample_image_file
        assert 'Content-Type' in file_response.headers
    
    def test_download_nonexistent_image(self, api_base_url, api_headers):
        """Test downloading non-existent image."""
        fake_id = 'non-existent-image-id-123'
        
        response = requests.get(
            f"{api_base_url}/images/{fake_id}/download",
            headers=api_headers
        )
        
        assert response.status_code in [404, 422]
        data = response.json()
        assert data['success'] is False
    
    def test_download_wrong_user(
        self, api_base_url, api_headers, created_image_with_upload, cleanup
    ):
        """Test downloading image belonging to different user."""
        image_id = created_image_with_upload['data']['image_id']
        
        # Try to download with different user
        wrong_user_headers = api_headers.copy()
        wrong_user_headers['User-Id'] = 'different-user-789'
        
        response = requests.get(
            f"{api_base_url}/images/{image_id}/download",
            headers=wrong_user_headers
        )
        
        # Should return 404 or 403
        assert response.status_code in [403, 404]
    
    def test_download_missing_user_id(
        self, api_base_url, created_image_with_upload, cleanup
    ):
        """Test downloading without user-id header."""
        image_id = created_image_with_upload['data']['image_id']
        
        response = requests.get(
            f"{api_base_url}/images/{image_id}/download",
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert data['success'] is False
    
    def test_download_metadata_only_image(
        self, api_base_url, api_headers, sample_image_metadata, cleanup
    ):
        """Test downloading image that has metadata but no S3 file yet."""
        # Create image metadata only (no S3 upload)
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=sample_image_metadata
        )
        image_id = response.json()['data']['image_id']
        
        # Try to download
        download_response = requests.get(
            f"{api_base_url}/images/{image_id}/download",
            headers=api_headers
        )
        
        # Should still generate presigned URL
        # (actual download might fail, but URL generation should succeed)
        assert download_response.status_code == 200
        assert 'presigned_url' in download_response.json()['data']
    
    def test_download_url_expiration_parameter(
        self, api_base_url, api_headers, created_image_with_upload, cleanup
    ):
        """Test download URL with custom expiration."""
        image_id = created_image_with_upload['data']['image_id']
        
        response = requests.get(
            f"{api_base_url}/images/{image_id}/download",
            headers=api_headers,
            params={'expiration': 300}  # 5 minutes
        )
        
        assert response.status_code == 200
        data = response.json()['data']
        assert 'presigned_url' in data
    
    def test_download_invalid_image_id(self, api_base_url, api_headers):
        """Test download with invalid image ID format."""
        invalid_ids = ['', '   ', '../../../etc/passwd']
        
        for invalid_id in invalid_ids:
            response = requests.get(
                f"{api_base_url}/images/{invalid_id}/download",
                headers=api_headers
            )
            
            assert response.status_code in [400, 403, 404, 422]
    
    def test_download_multiple_times(
        self, api_base_url, api_headers, created_image_with_upload, 
        sample_image_file, cleanup
    ):
        """Test that download URLs can be generated multiple times."""
        image_id = created_image_with_upload['data']['image_id']
        
        # Generate multiple download URLs
        urls = []
        for _ in range(3):
            response = requests.get(
                f"{api_base_url}/images/{image_id}/download",
                headers=api_headers
            )
            assert response.status_code == 200
            urls.append(response.json()['data']['presigned_url'])
        
        # All URLs should work
        for url in urls:
            file_response = requests.get(url)
            assert file_response.status_code == 200
            assert file_response.content == sample_image_file
