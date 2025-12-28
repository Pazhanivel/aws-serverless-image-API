# API Documentation

## mPyCloud Image Service API

**Version**: 1.0.0  
**Base URL**: `http://localhost:4566/dev` (LocalStack)  
**Protocol**: REST  
**Content-Type**: `application/json` (except upload endpoint)

**Status**: ✅ **Phase 3 Complete** - All 6 API endpoints implemented with handlers

---

## Table of Contents

1. [Authentication](#authentication)
2. [Error Handling](#error-handling)
3. [Endpoints](#endpoints)
   - [Upload Image](#1-upload-image)
   - [List Images](#2-list-images)
   - [Get Image Metadata](#3-get-image-metadata)
   - [Download Image](#4-download-image)
   - [Delete Image](#5-delete-image)
   - [Update Image Status](#6-update-image-status)
4. [Data Models](#data-models)
5. [Examples](#examples)
6. [Rate Limits](#rate-limits)

---

## Authentication

**Current Version**: No authentication (LocalStack development)

**Production**: Will use one of the following:
- AWS IAM authentication
- AWS Cognito User Pools
- API Keys via API Gateway

**Headers** (for future):
```
Authorization: Bearer <token>
X-API-Key: <api-key>
```

---

## Error Handling

### Error Response Format

All error responses follow this structure:

```json
{
    "error": "ErrorCode",
    "message": "Human-readable error description",
    "request_id": "uuid-v4",
    "timestamp": "2025-12-27T10:30:00Z"
}
```

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Successful GET/PUT request |
| 201 | Created | Resource successfully created |
| 204 | No Content | Successful DELETE (no body) |
| 400 | Bad Request | Invalid input parameters |
| 404 | Not Found | Resource not found |
| 413 | Payload Too Large | File size exceeds limit |
| 415 | Unsupported Media Type | Invalid file type |
| 422 | Unprocessable Entity | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Temporary unavailability |

### Common Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `INVALID_FILE_TYPE` | 415 | File type not supported |
| `FILE_TOO_LARGE` | 413 | File exceeds size limit |
| `IMAGE_NOT_FOUND` | 404 | Image does not exist |
| `UPLOAD_FAILED` | 500 | Upload operation failed |
| `DATABASE_ERROR` | 500 | Database operation failed |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |

---

## Endpoints

## 1. Upload Image

Upload an image with associated metadata.

### Request

**Method**: `POST`  
**Endpoint**: `/images`  
**Content-Type**: `multipart/form-data`

### Request Body (Form Data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | File | Yes | Image file (JPEG, PNG, GIF, WEBP) |
| `user_id` | String | Yes | User identifier |
| `description` | String | No | Image description (max 500 chars) |
| `tags` | JSON Array | No | Array of tags (max 20 tags) |
| `metadata` | JSON Object | No | Additional metadata |

### Constraints

- **File Size**: Maximum 10 MB
- **Supported Formats**: `image/jpeg`, `image/png`, `image/gif`, `image/webp`
- **Filename**: Max 255 characters
- **Tags**: Max 20 tags, each max 50 characters
- **Description**: Max 500 characters

### Response

**Status**: `201 Created`

```json
{
    "image_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "sunset.jpg",
    "size": 2048576,
    "content_type": "image/jpeg",
    "upload_timestamp": "2025-12-27T10:30:00Z",
    "s3_key": "images/user123/550e8400-e29b-41d4-a716-446655440000.jpg",
    "message": "Image uploaded successfully"
}
```

### Example Request (cURL)

**Basic upload:**
```bash
curl -X POST http://localhost:4566/dev/images \
  -H "Content-Type: application/json" \
  -H "User-Id: user123" \
  -d '{
    "filename": "sunset.jpg",
    "content_type": "image/jpeg",
    "description": "Beautiful sunset at the beach",
    "tags": ["sunset", "beach", "nature"]
  }'
```

**Upload with optional fields:**
```bash
curl -X POST http://localhost:4566/dev/images \
  -H "Content-Type: application/json" \
  -H "User-Id: user123" \
  -d '{
    "filename": "sunset.jpg",
    "content_type": "image/jpeg",
    "description": "Beautiful sunset",
    "tags": ["sunset", "beach"],
    "expiry": 1800
  }'
```

### Example Request (Python)

```python
import requests

url = "http://localhost:4566/dev/images"

files = {
    'image': open('sunset.jpg', 'rb')
}

data = {
    'user_id': 'user123',
    'description': 'Beautiful sunset at the beach',
    'tags': '["sunset", "beach", "nature"]',
    'metadata': '{"location": "California", "camera": "Canon EOS R5"}'
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### Error Responses

**Invalid File Type (415)**
```json
{
    "error": "INVALID_FILE_TYPE",
    "message": "File type 'image/bmp' is not supported. Allowed types: image/jpeg, image/png, image/gif, image/webp",
    "request_id": "req-123"
}
```

**File Too Large (413)**
```json
{
    "error": "FILE_TOO_LARGE",
    "message": "File size 12582912 bytes exceeds maximum allowed size of 10485760 bytes",
    "request_id": "req-124"
}
```

---

## 2. List Images

Retrieve a list of images with optional filtering.

### Request

**Method**: `GET`  
**Endpoint**: `/images`

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | String | No | Filter by user ID |
| `tags` | String | No | Comma-separated tags (e.g., "nature,sunset") |
| `content_type` | String | No | Filter by MIME type (e.g., "image/jpeg") |
| `start_date` | String | No | Start date (ISO 8601 format) |
| `end_date` | String | No | End date (ISO 8601 format) |
| `limit` | Integer | No | Number of results (default: 50, max: 100) |
| `last_key` | String | No | Pagination token from previous response |

### Filter Combinations

Filters can be combined using AND logic:
- `user_id` + `tags` → User's images with specific tags
- `user_id` + `start_date` + `end_date` → User's images in date range
- `content_type` + `tags` → Specific type with tags

### Response

**Status**: `200 OK`

```json
{
    "images": [
        {
            "image_id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "user123",
            "filename": "sunset.jpg",
            "content_type": "image/jpeg",
            "size": 2048576,
            "upload_timestamp": "2025-12-27T10:30:00Z",
            "tags": ["sunset", "beach", "nature"],
            "description": "Beautiful sunset at the beach",
            "width": 1920,
            "height": 1080,
            "metadata": {
                "location": "California",
                "camera": "Canon EOS R5"
            }
        },
        {
            "image_id": "660e8400-e29b-41d4-a716-446655440001",
            "user_id": "user123",
            "filename": "mountain.jpg",
            "content_type": "image/jpeg",
            "size": 3145728,
            "upload_timestamp": "2025-12-26T14:20:00Z",
            "tags": ["mountain", "landscape"],
            "description": "Mountain view",
            "width": 2560,
            "height": 1440
        }
    ],
    "count": 2,
    "total_count": 150,
    "last_evaluated_key": "eyJpbWFnZV9pZCI6ICI2NjBlODQwMC..."
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `images` | Array | List of image metadata objects |
| `count` | Integer | Number of images in current response |
| `total_count` | Integer | Total images matching filters (estimate) |
| `last_evaluated_key` | String | Pagination token (null if no more results) |

### Example Requests (cURL)

**List all images for a user:**
```bash
curl -X GET "http://localhost:4566/dev/images?limit=10" \
  -H "User-Id: user123"
```

**Filter by tags:**
```bash
curl -X GET "http://localhost:4566/dev/images?tag=sunset" \
  -H "User-Id: user123"
```

**Filter by date range:**
```bash
curl -X GET "http://localhost:4566/dev/images?start_date=2025-12-01T00:00:00Z&end_date=2025-12-31T23:59:59Z" \
  -H "User-Id: user123"
```

**Filter by content type:**
```bash
curl -X GET "http://localhost:4566/dev/images?content_type=image/png" \
  -H "User-Id: user123"
```

**Pagination:**
```bash
# First page
curl -X GET "http://localhost:4566/dev/images?limit=50" \
  -H "User-Id: user123"

# Next page (use next_token from previous response)
curl -X GET "http://localhost:4566/dev/images?limit=50&next_token=eyJpbWFnZV9pZCI6..." \
  -H "User-Id: user123"
```

**Pretty print results:**
```bash
curl -s -X GET "http://localhost:4566/dev/images" \
  -H "User-Id: user123" | jq '.data.items[] | {filename, size, status}'
```

### Example Request (Python)

```python
import requests

url = "http://localhost:4566/dev/images"

params = {
    'user_id': 'user123',
    'tags': 'sunset,nature',
    'limit': 20
}

response = requests.get(url, params=params)
data = response.json()

for image in data['images']:
    print(f"{image['filename']} - {image['upload_timestamp']}")

# Handle pagination
if data['last_evaluated_key']:
    params['last_key'] = data['last_evaluated_key']
    next_response = requests.get(url, params=params)
```

### Error Responses

**Invalid Query Parameter (400)**
```json
{
    "error": "VALIDATION_ERROR",
    "message": "Invalid date format for start_date. Expected ISO 8601 format.",
    "request_id": "req-125"
}
```

---

## 3. Get Image Metadata

Retrieve metadata for a specific image.

### Request

**Method**: `GET`  
**Endpoint**: `/images/{image_id}`

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_id` | String (UUID) | Yes | Unique image identifier |

### Response

**Status**: `200 OK`

```json
{
    "image_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user123",
    "filename": "sunset.jpg",
    "content_type": "image/jpeg",
    "size": 2048576,
    "s3_key": "images/user123/550e8400-e29b-41d4-a716-446655440000.jpg",
    "s3_bucket": "image-storage-bucket",
    "upload_timestamp": "2025-12-27T10:30:00Z",
    "tags": ["sunset", "beach", "nature"],
    "description": "Beautiful sunset at the beach",
    "width": 1920,
    "height": 1080,
    "status": "active",
    "metadata": {
        "location": "California",
        "camera": "Canon EOS R5",
        "iso": 100,
        "aperture": "f/8"
    }
}
```

### Example Requests (cURL)

**Basic request:**
```bash
curl -X GET http://localhost:4566/dev/images/550e8400-e29b-41d4-a716-446655440000 \
  -H "User-Id: user123"
```

**With formatted output:**
```bash
curl -X GET http://localhost:4566/dev/images/550e8400-e29b-41d4-a716-446655440000 \
  -H "User-Id: user123" \
  -H "Accept: application/json" | jq .
```

### Example Request (Python)

```python
import requests

image_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"http://localhost:4566/dev/images/{image_id}"

response = requests.get(url)
metadata = response.json()

print(f"Filename: {metadata['filename']}")
print(f"Size: {metadata['size']} bytes")
print(f"Tags: {', '.join(metadata['tags'])}")
```

### Error Responses

**Image Not Found (404)**
```json
{
    "error": "IMAGE_NOT_FOUND",
    "message": "Image with ID '550e8400-e29b-41d4-a716-446655440000' does not exist",
    "request_id": "req-126"
}
```

---

## 4. Download Image

Get a presigned URL to download or view the image.

### Request

**Method**: `GET`  
**Endpoint**: `/images/{image_id}/download`

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_id` | String (UUID) | Yes | Unique image identifier |

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `expires_in` | Integer | No | URL expiration time in seconds (default: 900, max: 3600) |
| `download` | Boolean | No | Force download vs inline display (default: false) |

### Response

**Status**: `200 OK`

**Option 1: JSON Response with Presigned URL**
```json
{
    "image_id": "550e8400-e29b-41d4-a716-446655440000",
    "download_url": "https://s3.amazonaws.com/image-storage-bucket/images/user123/550e8400...?AWSAccessKeyId=...&Signature=...&Expires=...",
    "expires_at": "2025-12-27T10:45:00Z",
    "content_type": "image/jpeg",
    "filename": "sunset.jpg"
}
```

**Option 2: HTTP Redirect (302)**
- Directly redirects to the presigned S3 URL
- Browser can display or download the image immediately

### Example Requests (cURL)

**Get download URL:**
```bash
curl -X GET http://localhost:4566/dev/images/550e8400-e29b-41d4-a716-446655440000/download \
  -H "User-Id: user123"
```

**Get URL with custom expiration:**
```bash
curl -X GET "http://localhost:4566/dev/images/550e8400-e29b-41d4-a716-446655440000/download?expires_in=1800" \
  -H "User-Id: user123"
```

**Force download (not inline):**
```bash
curl -X GET "http://localhost:4566/dev/images/550e8400-e29b-41d4-a716-446655440000/download?download=true" \
  -H "User-Id: user123"
```

**Direct download with redirect:**
```bash
curl -L -X GET http://localhost:4566/dev/images/550e8400-e29b-41d4-a716-446655440000/download \
  -H "User-Id: user123" \
  -o sunset.jpg
```

**Complete workflow - Get presigned URL and download:**
```bash
# Step 1: Get the presigned URL
DOWNLOAD_URL=$(curl -s -X GET http://localhost:4566/dev/images/550e8400-e29b-41d4-a716-446655440000/download \
  -H "User-Id: user123" | jq -r '.data.presigned_url')

# Step 2: Download the file using the presigned URL
curl -o image.jpg "$DOWNLOAD_URL"
```

### Example Request (Python)

```python
import requests

image_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"http://localhost:4566/dev/images/{image_id}/download"

# Get presigned URL
response = requests.get(url)
data = response.json()
download_url = data['download_url']

# Download the image
image_response = requests.get(download_url)
with open('downloaded_image.jpg', 'wb') as f:
    f.write(image_response.content)

print(f"Image downloaded: {data['filename']}")
```

### Error Responses

**Image Not Found (404)**
```json
{
    "error": "IMAGE_NOT_FOUND",
    "message": "Image with ID '550e8400-e29b-41d4-a716-446655440000' does not exist",
    "request_id": "req-127"
}
```

---

## 5. Delete Image

Delete an image and its metadata.

### Request

**Method**: `DELETE`  
**Endpoint**: `/images/{image_id}`

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_id` | String (UUID) | Yes | Unique image identifier |

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `hard_delete` | Boolean | No | Permanently delete (default: false, soft delete) |

### Response

**Status**: `204 No Content` (no response body)

**Or with confirmation:**

**Status**: `200 OK`
```json
{
    "message": "Image deleted successfully",
    "image_id": "550e8400-e29b-41d4-a716-446655440000",
    "deleted_at": "2025-12-27T10:30:00Z"
}
```

### Delete Strategies

**Soft Delete (default)**:
- Updates `status` field to "deleted" in DynamoDB
- Image remains in S3 (can be recovered)
- Excluded from list queries
- Recommended for production

**Hard Delete**:
- Permanently removes from both S3 and DynamoDB
- Cannot be recovered
- Use with caution

### Example Requests (cURL)

**Soft delete:**
```bash
curl -X DELETE http://localhost:4566/dev/images/550e8400-e29b-41d4-a716-446655440000 \
  -H "User-Id: user123"
```

**Hard delete:**
```bash
curl -X DELETE "http://localhost:4566/dev/images/550e8400-e29b-41d4-a716-446655440000?hard_delete=true" \
  -H "User-Id: user123"
```

**Delete with verbose output:**
```bash
curl -v -X DELETE http://localhost:4566/dev/images/550e8400-e29b-41d4-a716-446655440000 \
  -H "User-Id: user123"
```

**Bulk delete script:**
```bash
# Delete multiple images
for image_id in img-id-1 img-id-2 img-id-3; do
  curl -X DELETE "http://localhost:4566/dev/images/$image_id?hard_delete=true" \
    -H "User-Id: user123"
  echo "Deleted: $image_id"
done
```

### Example Request (Python)

```python
import requests

image_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"http://localhost:4566/dev/images/{image_id}"

# Soft delete
response = requests.delete(url)
if response.status_code == 204:
    print("Image deleted successfully")

# Hard delete
response = requests.delete(url, params={'hard_delete': True})
```

### Error Responses

**Image Not Found (404)**
```json
{
    "error": "IMAGE_NOT_FOUND",
    "message": "Image with ID '550e8400-e29b-41d4-a716-446655440000' does not exist or already deleted",
    "request_id": "req-128"
}
```

**Unauthorized (403)**
```json
{
    "error": "FORBIDDEN",
    "message": "You do not have permission to delete this image",
    "request_id": "req-129"
}
```

---

## 6. Update Image Status

Update the status of an image after uploading to S3 (typically to mark as 'active').

### Request

**Method**: `PATCH`  
**Endpoint**: `/images/{image_id}`

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_id` | String (UUID) | Yes | Unique image identifier |

### Request Body

```json
{
    "status": "active",
    "size": 1234567,
    "width": 1920,
    "height": 1080
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | String | Yes | New status: "active", "processing", or "error" |
| `size` | Number | No | File size in bytes (detected from S3 if not provided) |
| `width` | Number | No | Image width in pixels |
| `height` | Number | No | Image height in pixels |

### Response

**Status**: `200 OK`
```json
{
    "image_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "active",
    "size": 1234567,
    "width": 1920,
    "height": 1080,
    "message": "Image status updated successfully"
}
```

### Usage Flow

1. Client requests presigned URL: `POST /images`
2. Client uploads file to S3 using presigned URL
3. Client confirms upload: `PATCH /images/{image_id}` with `status=active`
4. System verifies S3 file exists and updates metadata

### Example Requests (cURL)

**Basic status update:**
```bash
curl -X PATCH http://localhost:4566/dev/images/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -H "User-Id: user123" \
  -d '{"status": "active"}'
```

**With dimensions:**
```bash
curl -X PATCH http://localhost:4566/dev/images/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -H "User-Id: user123" \
  -d '{
    "status": "active",
    "size": 1234567,
    "width": 1920,
    "height": 1080
  }'
```

**Mark as error status:**
```bash
curl -X PATCH http://localhost:4566/dev/images/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -H "User-Id: user123" \
  -d '{"status": "error"}'
```

**Complete upload workflow:**
```bash
# Step 1: Request presigned URL
RESPONSE=$(curl -s -X POST http://localhost:4566/dev/images \
  -H "Content-Type: application/json" \
  -H "User-Id: user123" \
  -d '{
    "filename": "photo.jpg",
    "content_type": "image/jpeg"
  }')

# Extract values
IMAGE_ID=$(echo $RESPONSE | jq -r '.data.image_id')
UPLOAD_URL=$(echo $RESPONSE | jq -r '.data.upload_url')

# Step 2: Upload file to S3
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: image/jpeg" \
  --data-binary @photo.jpg

# Step 3: Update status to active
curl -X PATCH "http://localhost:4566/dev/images/$IMAGE_ID" \
  -H "Content-Type: application/json" \
  -H "User-Id: user123" \
  -d '{
    "status": "active",
    "size": 1234567,
    "width": 1920,
    "height": 1080
  }'
```

### Example Request (Python)

```python
import requests

image_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"http://localhost:4566/dev/images/{image_id}"

# After uploading to S3, mark as active
response = requests.patch(
    url,
    headers={"User-Id": "user123"},
    json={
        "status": "active",
        "size": 1234567,
        "width": 1920,
        "height": 1080
    }
)

if response.status_code == 200:
    print("Status updated successfully")
    print(response.json())
```

### Error Responses

**Image Not Found (404)**
```json
{
    "error": "IMAGE_NOT_FOUND",
    "message": "Image not found: 550e8400-e29b-41d4-a716-446655440000",
    "request_id": "req-130"
}
```

**Invalid Status (400)**
```json
{
    "error": "VALIDATION_ERROR",
    "message": "Invalid status. Must be one of: active, processing, error",
    "request_id": "req-131"
}
```

**S3 File Not Found (400)**
```json
{
    "error": "FILE_NOT_FOUND",
    "message": "Cannot set status to active: file not found in S3. Please upload the file first.",
    "request_id": "req-132"
}
```

**Cannot Update Deleted Image (409)**
```json
{
    "error": "CONFLICT",
    "message": "Cannot update status of deleted image",
    "request_id": "req-133"
}
```

---

## Data Models

### ImageMetadata Object

Complete structure of the image metadata object:

```typescript
{
    image_id: string (UUID v4),           // Unique identifier
    user_id: string,                      // User who uploaded
    filename: string,                     // Original filename
    content_type: string,                 // MIME type
    size: number,                         // Size in bytes
    s3_key: string,                       // S3 object key
    s3_bucket: string,                    // S3 bucket name
    upload_timestamp: string (ISO 8601),  // Upload date/time
    tags: string[],                       // Array of tags
    description?: string,                 // Optional description
    width?: number,                       // Image width in pixels
    height?: number,                      // Image height in pixels
    status: string,                       // "active" | "deleted"
    metadata?: {                          // Optional custom metadata
        [key: string]: any
    }
}
```

### Validation Rules

| Field | Validation |
|-------|------------|
| `image_id` | UUID v4 format |
| `user_id` | 3-100 characters, alphanumeric + underscore |
| `filename` | 1-255 characters, valid filename characters |
| `content_type` | One of: image/jpeg, image/png, image/gif, image/webp |
| `size` | 1 byte - 10 MB (10485760 bytes) |
| `tags` | Array of 0-20 strings, each 1-50 characters |
| `description` | 0-500 characters |
| `upload_timestamp` | ISO 8601 format (UTC) |

---

## Examples

### Complete Workflow Example

```python
import requests
import json

BASE_URL = "http://localhost:4566/dev"
USER_ID = "user123"

# 1. Upload an image
print("1. Uploading image...")
with open('sunset.jpg', 'rb') as image_file:
    files = {'image': image_file}
    data = {
        'user_id': USER_ID,
        'description': 'Beautiful sunset',
        'tags': json.dumps(['sunset', 'nature', 'beach'])
    }
    response = requests.post(f"{BASE_URL}/images", files=files, data=data)
    upload_result = response.json()
    image_id = upload_result['image_id']
    print(f"   Uploaded: {image_id}")

# 2. List user's images
print("\n2. Listing images...")
response = requests.get(f"{BASE_URL}/images", params={'user_id': USER_ID})
images = response.json()
print(f"   Found {images['count']} images")
for img in images['images']:
    print(f"   - {img['filename']} ({img['size']} bytes)")

# 3. Get specific image metadata
print(f"\n3. Getting metadata for {image_id}...")
response = requests.get(f"{BASE_URL}/images/{image_id}")
metadata = response.json()
print(f"   Filename: {metadata['filename']}")
print(f"   Size: {metadata['size']} bytes")
print(f"   Dimensions: {metadata.get('width')}x{metadata.get('height')}")
print(f"   Tags: {', '.join(metadata['tags'])}")

# 4. Download the image
print(f"\n4. Downloading image...")
response = requests.get(f"{BASE_URL}/images/{image_id}/download")
download_data = response.json()
download_url = download_data['download_url']

# Actually download the file
image_response = requests.get(download_url)
with open('downloaded_sunset.jpg', 'wb') as f:
    f.write(image_response.content)
print(f"   Downloaded to: downloaded_sunset.jpg")

# 5. Filter images by tags
print("\n5. Filtering by tags...")
response = requests.get(f"{BASE_URL}/images", params={
    'user_id': USER_ID,
    'tags': 'sunset,nature'
})
filtered = response.json()
print(f"   Found {filtered['count']} images with tags 'sunset' and 'nature'")

# 6. Delete the image
print(f"\n6. Deleting image {image_id}...")
response = requests.delete(f"{BASE_URL}/images/{image_id}")
if response.status_code == 204:
    print("   Deleted successfully")

# 7. Verify deletion
print("\n7. Verifying deletion...")
response = requests.get(f"{BASE_URL}/images/{image_id}")
if response.status_code == 404:
    print("   Image no longer exists")
```

### Batch Upload Example

```python
import requests
import os
import json
from pathlib import Path

BASE_URL = "http://localhost:4566/dev"
USER_ID = "user123"
IMAGE_DIR = "./photos"

def upload_image(filepath, tags=None):
    """Upload a single image with tags"""
    filename = os.path.basename(filepath)
    
    with open(filepath, 'rb') as f:
        files = {'image': f}
        data = {
            'user_id': USER_ID,
            'description': f'Uploaded from {filename}',
            'tags': json.dumps(tags or [])
        }
        
        response = requests.post(f"{BASE_URL}/images", files=files, data=data)
        
        if response.status_code == 201:
            result = response.json()
            print(f"✓ Uploaded: {filename} -> {result['image_id']}")
            return result
        else:
            print(f"✗ Failed: {filename} - {response.json()}")
            return None

# Upload all images in directory
image_files = Path(IMAGE_DIR).glob("*.jpg")
results = []

for image_path in image_files:
    # Auto-tag based on filename
    tags = ['vacation', 'summer']
    if 'beach' in str(image_path).lower():
        tags.append('beach')
    if 'sunset' in str(image_path).lower():
        tags.append('sunset')
    
    result = upload_image(str(image_path), tags)
    if result:
        results.append(result)

print(f"\nUploaded {len(results)} images successfully")
```

### Search and Filter Example

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:4566/dev"

def search_images(**filters):
    """Search images with various filters"""
    response = requests.get(f"{BASE_URL}/images", params=filters)
    return response.json()

# Example 1: Find all images for a user
user_images = search_images(user_id='user123', limit=100)
print(f"User has {user_images['count']} images")

# Example 2: Find images by tags
nature_images = search_images(
    user_id='user123',
    tags='nature,landscape'
)
print(f"Found {nature_images['count']} nature images")

# Example 3: Find images from last 7 days
week_ago = (datetime.now() - timedelta(days=7)).isoformat() + 'Z'
recent_images = search_images(
    user_id='user123',
    start_date=week_ago
)
print(f"Found {recent_images['count']} recent images")

# Example 4: Find PNG images
png_images = search_images(
    user_id='user123',
    content_type='image/png'
)
print(f"Found {png_images['count']} PNG images")

# Example 5: Paginate through all results
all_images = []
last_key = None

while True:
    params = {'user_id': 'user123', 'limit': 50}
    if last_key:
        params['last_key'] = last_key
    
    result = search_images(**params)
    all_images.extend(result['images'])
    
    last_key = result.get('last_evaluated_key')
    if not last_key:
        break

print(f"Retrieved all {len(all_images)} images")
```

---

## Rate Limits

### Current Limits (LocalStack Development)

No rate limits enforced in local development.

### Production Recommendations

| Endpoint | Rate Limit | Burst |
|----------|------------|-------|
| Upload | 10 requests/minute | 20 |
| List | 100 requests/minute | 200 |
| Get | 100 requests/minute | 200 |
| Download | 50 requests/minute | 100 |
| Delete | 20 requests/minute | 30 |

### Rate Limit Headers (Future)

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640606400
```

### Rate Limit Exceeded Response

**Status**: `429 Too Many Requests`

```json
{
    "error": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 45 seconds.",
    "retry_after": 45,
    "request_id": "req-130"
}
```

---

## Best Practices

### 1. Error Handling

Always check HTTP status codes and handle errors appropriately:

```python
response = requests.post(url, files=files, data=data)

if response.status_code == 201:
    result = response.json()
    print(f"Success: {result['image_id']}")
elif response.status_code == 413:
    print("Error: File too large")
elif response.status_code == 415:
    print("Error: Invalid file type")
else:
    error = response.json()
    print(f"Error: {error['message']}")
```

### 2. Pagination

Always implement pagination for list operations:

```python
def get_all_images(user_id):
    images = []
    last_key = None
    
    while True:
        params = {'user_id': user_id, 'limit': 100}
        if last_key:
            params['last_key'] = last_key
        
        response = requests.get(url, params=params)
        data = response.json()
        
        images.extend(data['images'])
        last_key = data.get('last_evaluated_key')
        
        if not last_key:
            break
    
    return images
```

### 3. Presigned URL Expiration

Download presigned URLs before they expire:

```python
# Get download URL
response = requests.get(f"{BASE_URL}/images/{image_id}/download")
data = response.json()

# Check expiration
from datetime import datetime
expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
if datetime.now() < expires_at:
    # URL is still valid
    image_data = requests.get(data['download_url']).content
```

### 4. Retry Logic

Implement exponential backoff for transient errors:

```python
import time

def upload_with_retry(file_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            with open(file_path, 'rb') as f:
                files = {'image': f}
                data = {'user_id': 'user123'}
                response = requests.post(url, files=files, data=data)
                
                if response.status_code == 201:
                    return response.json()
                elif response.status_code >= 500:
                    # Server error, retry
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    # Client error, don't retry
                    raise Exception(response.json()['message'])
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
```

---

## Postman Collection

Import this collection into Postman for easy API testing:

**File**: `postman_collection.json` (included in repository)

**Quick Test:**
1. Import collection into Postman
2. Set `base_url` variable to `http://localhost:4566/dev`
3. Run the collection to test all endpoints

---

## Support & Resources

- **GitHub Repository**: [Link to repository]
- **Issue Tracker**: [Link to issues]
- **Documentation**: This file
- **Design Document**: `DESIGN.md`
- **Implementation Plan**: `IMPLEMENTATION_PLAN.md`

---

## Changelog

### Version 1.0.0 (2025-12-27)
- Initial API release
- Upload, list, get, download, delete endpoints
- Support for user_id and tags filtering
- Presigned URL generation
- Soft and hard delete options

---

## Future API Enhancements

### Planned Features

1. **Batch Operations**
   - `POST /images/batch` - Upload multiple images
   - `DELETE /images/batch` - Delete multiple images

2. **Image Processing**
   - `POST /images/{id}/resize` - Resize image
   - `GET /images/{id}/thumbnail` - Get thumbnail
   - `POST /images/{id}/convert` - Convert format

3. **Advanced Search**
   - Full-text search in descriptions
   - Image similarity search
   - Facial recognition

4. **Social Features**
   - `POST /images/{id}/like` - Like an image
   - `GET /images/{id}/comments` - Get comments
   - `POST /images/{id}/share` - Share image

5. **Analytics**
   - `GET /images/{id}/stats` - View counts, likes
   - `GET /users/{id}/stats` - User statistics

---

**Last Updated**: December 27, 2025  
**API Version**: 1.0.0  
**Maintained By**: Development Team
