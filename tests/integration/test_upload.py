"""
Integration tests for upload endpoint.
"""

import pytest
import requests
import json


class TestUploadEndpoint:
    """Test cases for POST /images endpoint."""
    
    def test_upload_successful_presigned_url_generation(
        self, api_base_url, api_headers, sample_image_metadata, s3_client, cleanup
    ):
        """Test successful generation of presigned upload URL."""
        # Request presigned URL
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=sample_image_metadata
        )
        
        assert response.status_code == 201
        response_data = response.json()
        
        # Verify response structure
        assert response_data['success'] is True
        assert 'data' in response_data
        assert 'message' in response_data
        
        data = response_data['data']
        assert 'image_id' in data
        assert 'upload_url' in data
        assert 's3_key' in data
        
        # Verify upload URL is valid
        assert data['upload_url'].startswith('http')
        assert 'image-storage-bucket' in data['upload_url']
    
    def test_upload_and_s3_upload(
        self, api_base_url, api_headers, sample_image_metadata, 
        sample_image_file, s3_client, cleanup
    ):
        """Test full upload flow: get presigned URL and upload to S3."""
        # Step 1: Get presigned URL
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=sample_image_metadata
        )
        
        assert response.status_code == 201
        response_data = response.json()
        data = response_data['data']
        upload_url = data['upload_url']
        image_id = data['image_id']
        s3_key = data['s3_key']
        
        # Step 2: Upload file to S3 using presigned URL
        upload_response = requests.put(
            upload_url,
            data=sample_image_file,
            headers={'Content-Type': sample_image_metadata['content_type']}
        )
        
        assert upload_response.status_code in [200, 204]
        
        # Step 3: Verify file exists in S3
        try:
            obj = s3_client.get_object(
                Bucket='image-storage-bucket',
                Key=s3_key
            )
            assert obj['ContentType'] == sample_image_metadata['content_type']
            assert obj['Body'].read() == sample_image_file
        except Exception as e:
            pytest.fail(f"Failed to verify S3 upload: {str(e)}")
    
    def test_upload_missing_filename(self, api_base_url, api_headers):
        """Test upload with missing filename."""
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json={'content_type': 'image/jpeg'}
        )
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert data['success'] is False
        assert 'message' in data or 'details' in data
    
    def test_upload_missing_content_type(self, api_base_url, api_headers):
        """Test upload with missing content type."""
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json={'filename': 'test.jpg'}
        )
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert data['success'] is False
        assert 'message' in data or 'details' in data
    
    def test_upload_invalid_content_type(self, api_base_url, api_headers):
        """Test upload with invalid content type."""
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json={
                'filename': 'test.txt',
                'content_type': 'text/plain'
            }
        )
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert data['success'] is False
        assert 'message' in data or 'details' in data
    
    def test_upload_missing_user_id(self, api_base_url, sample_image_metadata):
        """Test upload without user-id header."""
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            f"{api_base_url}/images",
            headers=headers,
            json=sample_image_metadata
        )
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert data['success'] is False
        assert 'message' in data or 'details' in data
    
    def test_upload_with_tags(
        self, api_base_url, api_headers, cleanup
    ):
        """Test upload with multiple tags."""
        metadata = {
            'filename': 'tagged-image.jpg',
            'content_type': 'image/jpeg',
            'tags': ['vacation', 'beach', 'sunset', '2024']
        }
        
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=metadata
        )
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data['success'] is True
        data = response_data['data']
        assert 'image_id' in data
    
    def test_upload_with_description(
        self, api_base_url, api_headers, cleanup
    ):
        """Test upload with description."""
        metadata = {
            'filename': 'described-image.jpg',
            'content_type': 'image/jpeg',
            'description': 'A beautiful sunset over the ocean'
        }
        
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=metadata
        )
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data['success'] is True
        data = response_data['data']
        assert 'image_id' in data
    
    def test_upload_png_image(self, api_base_url, api_headers, cleanup):
        """Test upload with PNG content type."""
        metadata = {
            'filename': 'test-image.png',
            'content_type': 'image/png'
        }
        
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=metadata
        )
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data['success'] is True
        data = response_data['data']
        assert 'image_id' in data
    
    def test_upload_gif_image(self, api_base_url, api_headers, cleanup):
        """Test upload with GIF content type."""
        metadata = {
            'filename': 'animated.gif',
            'content_type': 'image/gif'
        }
        
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=metadata
        )
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data['success'] is True
        data = response_data['data']
        assert 'image_id' in data
