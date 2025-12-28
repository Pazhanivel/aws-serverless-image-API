"""
End-to-end workflow integration tests.
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


class TestE2EWorkflows:
    """Test complete end-to-end workflows."""
    
    def test_complete_upload_download_delete_workflow(
        self, api_base_url, api_headers, sample_image_metadata, 
        sample_image_file, cleanup
    ):
        """Test complete workflow: upload -> download -> delete."""
        # Step 1: Request presigned upload URL
        upload_response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=sample_image_metadata
        )
        assert upload_response.status_code == 201
        upload_data = upload_response.json()['data']
        image_id = upload_data['image_id']
        upload_url = upload_data['upload_url']
        
        # Step 2: Upload file to S3
        s3_response = requests.put(
            upload_url,
            data=sample_image_file,
            headers={'Content-Type': sample_image_metadata['content_type']}
        )
        assert s3_response.status_code in [200, 204]
        
        # Step 3: Get metadata
        get_response = requests.get(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        assert get_response.status_code == 200
        metadata = get_response.json()['data']
        assert metadata['filename'] == sample_image_metadata['filename']
        
        # Step 4: Download file
        download_response = requests.get(
            f"{api_base_url}/images/{image_id}/download",
            headers=api_headers
        )
        assert download_response.status_code == 200
        download_url = download_response.json()['data']['presigned_url']
        
        file_response = requests.get(download_url)
        assert file_response.status_code == 200
        assert file_response.content == sample_image_file
        
        # Step 5: Delete image
        delete_response = requests.delete(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers,
            params={'hard_delete': 'true'}
        )
        assert delete_response.status_code == 200
        
        # Step 6: Verify deletion
        verify_response = requests.get(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        assert verify_response.status_code == 404
    
    def test_multiple_images_workflow(
        self, api_base_url, api_headers, sample_image_file, cleanup
    ):
        """Test workflow with multiple images."""
        image_ids = []
        
        # Upload multiple images
        for i in range(3):
            metadata = {
                'filename': f'test-image-{i}.jpg',
                'content_type': 'image/jpeg',
                'tags': [f'batch-{i}', 'test']
            }
            
            # Create metadata
            response = requests.post(
                f"{api_base_url}/images",
                headers=api_headers,
                json=metadata
            )
            assert response.status_code == 201
            data = response.json()['data']
            image_ids.append(data['image_id'])
            
            # Upload file
            requests.put(
                data['upload_url'],
                data=sample_image_file,
                headers={'Content-Type': metadata['content_type']}
            )
            
            time.sleep(0.1)
        
        # List all images - wait for DynamoDB eventual consistency
        list_response = wait_for_list_results(api_base_url, api_headers, min_count=3)
        assert list_response.status_code == 200
        images = list_response.json()['data']['items']
        
        # Verify all uploaded images are in the list
        listed_ids = {img['image_id'] for img in images}
        for image_id in image_ids:
            assert image_id in listed_ids
        
        # Download each image
        for image_id in image_ids:
            download_response = requests.get(
                f"{api_base_url}/images/{image_id}/download",
                headers=api_headers
            )
            assert download_response.status_code == 200
            
            download_url = download_response.json()['data']['presigned_url']
            file_response = requests.get(download_url)
            assert file_response.status_code == 200
        
        # Delete all images
        for image_id in image_ids:
            delete_response = requests.delete(
                f"{api_base_url}/images/{image_id}",
                headers=api_headers,
                params={'hard_delete': 'true'}
            )
            assert delete_response.status_code == 200
    
    def test_tag_based_search_workflow(
        self, api_base_url, api_headers, sample_image_file, cleanup
    ):
        """Test workflow with tag-based searching."""
        # Upload images with different tags
        vacation_images = []
        work_images = []
        
        for i in range(2):
            # Vacation image
            vacation_meta = {
                'filename': f'vacation-{i}.jpg',
                'content_type': 'image/jpeg',
                'tags': ['vacation', 'beach']
            }
            response = requests.post(
                f"{api_base_url}/images",
                headers=api_headers,
                json=vacation_meta
            )
            vacation_images.append(response.json()['data']['image_id'])
            
            # Work image
            work_meta = {
                'filename': f'work-{i}.jpg',
                'content_type': 'image/jpeg',
                'tags': ['work', 'office']
            }
            response = requests.post(
                f"{api_base_url}/images",
                headers=api_headers,
                json=work_meta
            )
            work_images.append(response.json()['data']['image_id'])
            
            time.sleep(0.1)
        
        # Search for vacation images - wait for DynamoDB eventual consistency
        vacation_list = wait_for_list_results(
            api_base_url, api_headers, min_count=2, tag='vacation'
        )
        assert vacation_list.status_code == 200
        vacation_results = [img['image_id'] for img in vacation_list.json()['data']['items']]
        
        for img_id in vacation_images:
            assert img_id in vacation_results
        
        # Search for work images
        work_list = requests.get(
            f"{api_base_url}/images",
            headers=api_headers,
            params={'tag': 'work'}
        )
        assert work_list.status_code == 200
        work_results = [img['image_id'] for img in work_list.json()['data']['items']]
        
        for img_id in work_images:
            assert img_id in work_results
    
    def test_pagination_workflow(
        self, api_base_url, api_headers, cleanup
    ):
        """Test pagination workflow."""
        # Create 5 images
        created_ids = []
        for i in range(5):
            metadata = {
                'filename': f'paginated-{i}.jpg',
                'content_type': 'image/jpeg'
            }
            response = requests.post(
                f"{api_base_url}/images",
                headers=api_headers,
                json=metadata
            )
            created_ids.append(response.json()['data']['image_id'])
            time.sleep(0.1)
        
        # Wait for DynamoDB eventual consistency before pagination
        time.sleep(5)
        
        # Fetch with pagination (2 per page)
        all_fetched_ids = []
        next_token = None
        
        while True:
            params = {'limit': 2}
            if next_token:
                params['next_token'] = next_token
            
            response = requests.get(
                f"{api_base_url}/images",
                headers=api_headers,
                params=params
            )
            assert response.status_code == 200
            data = response.json()['data']
            
            # Collect IDs
            for img in data['items']:
                all_fetched_ids.append(img['image_id'])
            
            # Check for more pages
            if data.get('has_more') and 'next_token' in data:
                next_token = data['next_token']
            else:
                break
        
        # Verify all images were fetched
        for created_id in created_ids:
            assert created_id in all_fetched_ids
    
    def test_error_recovery_workflow(
        self, api_base_url, api_headers, sample_image_metadata, cleanup
    ):
        """Test error handling and recovery."""
        # Try to get non-existent image
        response = requests.get(
            f"{api_base_url}/images/fake-id-123",
            headers=api_headers
        )
        assert response.status_code in [404, 422]
        
        # Try invalid upload
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json={'filename': 'test.txt', 'content_type': 'text/plain'}
        )
        assert response.status_code in [400, 422]
        
        # Valid upload after errors
        response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=sample_image_metadata
        )
        assert response.status_code == 201
    
    def test_concurrent_operations_workflow(
        self, api_base_url, api_headers, sample_image_metadata, 
        sample_image_file, cleanup
    ):
        """Test concurrent operations on same image."""
        # Create image
        create_response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=sample_image_metadata
        )
        image_id = create_response.json()['data']['image_id']
        
        # Multiple concurrent gets (should all succeed)
        responses = []
        for _ in range(3):
            response = requests.get(
                f"{api_base_url}/images/{image_id}",
                headers=api_headers
            )
            responses.append(response)
        
        for response in responses:
            assert response.status_code == 200
            assert response.json()['data']['image_id'] == image_id
    
    def test_full_image_lifecycle_with_s3_upload(
        self, api_base_url, api_headers, sample_image_metadata,
        sample_image_file, s3_client, cleanup
    ):
        """
        Test complete image lifecycle with actual S3 upload:
        1. Request presigned URL
        2. Upload actual image to S3
        3. Update status to active
        4. Verify image in S3
        5. Download and validate content
        6. Delete with S3 cleanup
        """
        # Step 1: Request presigned upload URL
        upload_response = requests.post(
            f"{api_base_url}/images",
            headers=api_headers,
            json=sample_image_metadata
        )
        assert upload_response.status_code == 201
        upload_data = upload_response.json()['data']
        
        image_id = upload_data['image_id']
        upload_url = upload_data['upload_url']
        s3_key = upload_data['s3_key']
        
        # Verify metadata shows processing status
        assert upload_data['metadata']['status'] == 'processing'
        assert upload_data['metadata']['filename'] == sample_image_metadata['filename']
        
        # Step 2: Upload actual file to S3 using presigned URL
        s3_upload_response = requests.put(
            upload_url,
            data=sample_image_file,
            headers={'Content-Type': sample_image_metadata['content_type']}
        )
        assert s3_upload_response.status_code in [200, 204], \
            f"S3 upload failed with status {s3_upload_response.status_code}"
        
        # Step 3: Verify file exists in S3 immediately after upload
        file_size = len(sample_image_file)
        try:
            s3_object = s3_client.get_object(
                Bucket='image-storage-bucket',
                Key=s3_key
            )
            s3_content = s3_object['Body'].read()
            assert s3_content == sample_image_file, \
                f"S3 content doesn't match uploaded file. Expected {len(sample_image_file)} bytes, got {len(s3_content)} bytes"
            assert len(s3_content) == file_size, \
                f"File size mismatch in S3. Expected {file_size}, got {len(s3_content)}"
            
            # Verify content type
            assert s3_object['ContentType'] == sample_image_metadata['content_type'], \
                f"Content type mismatch. Expected {sample_image_metadata['content_type']}, got {s3_object['ContentType']}"
        except s3_client.exceptions.NoSuchKey:
            pytest.fail(f"File not found in S3 immediately after upload. Key: {s3_key}")
        except Exception as e:
            pytest.fail(f"Failed to verify S3 upload: {str(e)}")
        
        # Step 3b: Verify file can be downloaded via the presigned upload URL (GET request)
        # Note: Some presigned URLs allow GET as well as PUT
        verify_download_response = requests.get(upload_url)
        if verify_download_response.status_code == 200:
            # If GET is allowed on upload URL, verify content
            assert verify_download_response.content == sample_image_file, \
                "Content from presigned upload URL doesn't match original"
        
        # Step 4: Update image status to active with dimensions
        update_response = requests.patch(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers,
            json={
                'status': 'active',
                'size': file_size,
                'width': 800,
                'height': 600
            }
        )
        assert update_response.status_code == 200
        update_data = update_response.json()['data']
        assert update_data['status'] == 'active'
        assert update_data['size'] == file_size
        assert update_data['width'] == 800
        assert update_data['height'] == 600
        
        # Step 5: Get updated metadata
        metadata_response = requests.get(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        assert metadata_response.status_code == 200
        metadata = metadata_response.json()['data']
        assert metadata['status'] == 'active'
        assert metadata['size'] == file_size
        assert metadata['width'] == 800
        assert metadata['height'] == 600
        assert metadata['filename'] == sample_image_metadata['filename']
        
        # Step 6: Download image via API and verify presigned download URL works
        download_response = requests.get(
            f"{api_base_url}/images/{image_id}/download",
            headers=api_headers
        )
        assert download_response.status_code == 200
        download_url = download_response.json()['data']['presigned_url']
        
        # Verify the presigned download URL is valid and accessible
        assert download_url.startswith('http'), "Download URL should be a valid HTTP URL"
        assert 'image-storage-bucket' in download_url, "Download URL should reference the S3 bucket"
        
        # Download actual file using presigned URL
        file_download = requests.get(download_url)
        assert file_download.status_code == 200, \
            f"Failed to download file from presigned URL. Status: {file_download.status_code}"
        assert file_download.content == sample_image_file, \
            f"Downloaded content doesn't match original. Expected {len(sample_image_file)} bytes, got {len(file_download.content)} bytes"
        assert len(file_download.content) == file_size, \
            f"Downloaded file size mismatch. Expected {file_size}, got {len(file_download.content)}"
        
        # Verify content type in download response
        assert file_download.headers.get('Content-Type') == sample_image_metadata['content_type'], \
            f"Downloaded file content type mismatch"
        
        # Step 7: List images and verify this image appears
        list_response = wait_for_list_results(api_base_url, api_headers, min_count=1)
        assert list_response.status_code == 200
        images = list_response.json()['data']['items']
        image_ids = [img['image_id'] for img in images]
        assert image_id in image_ids, "Image not found in list"
        
        # Step 8: Hard delete (removes from both DynamoDB and S3)
        delete_response = requests.delete(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers,
            params={'hard_delete': 'true'}
        )
        assert delete_response.status_code == 200
        
        # Step 9: Verify complete deletion
        # Check API returns 404
        verify_api = requests.get(
            f"{api_base_url}/images/{image_id}",
            headers=api_headers
        )
        assert verify_api.status_code == 404
        
        # Check S3 file is deleted
        try:
            s3_client.get_object(
                Bucket='image-storage-bucket',
                Key=s3_key
            )
            pytest.fail("S3 object should have been deleted but still exists")
        except s3_client.exceptions.NoSuchKey:
            pass  # Expected - file was deleted

