# Image Service Design Document

## Project Overview

A scalable, cloud-native image management service similar to Instagram, built using AWS serverless architecture with Python 3.7+. The service supports concurrent multi-user operations for uploading, storing, retrieving, searching, and deleting images with associated metadata.

## System Architecture

### High-Level Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Gateway    │  (REST API Endpoints)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Lambda Functions│  (Business Logic)
└────┬───────┬────┘
     │       │
     ▼       ▼
┌────────┐ ┌──────────┐
│   S3   │ │ DynamoDB │
└────────┘ └──────────┘
 (Images)   (Metadata)
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Layer | API Gateway | RESTful API endpoints, request routing |
| Compute | AWS Lambda | Serverless functions for business logic |
| Storage | Amazon S3 | Object storage for images |
| Database | DynamoDB | NoSQL database for metadata |
| Language | Python 3.7+ | Backend implementation |
| Local Dev | LocalStack | Local AWS service emulation |
| Testing | pytest, moto | Unit and integration testing |

## Design Decisions

### 1. Serverless Architecture

**Rationale:**
- **Scalability**: Lambda automatically scales with concurrent requests
- **Cost-Effective**: Pay only for actual execution time
- **Maintenance**: No server management required
- **High Availability**: Built-in redundancy and fault tolerance

### 2. S3 for Image Storage

**Rationale:**
- Designed for large object storage
- Highly durable (99.999999999% durability)
- Supports presigned URLs for secure direct uploads/downloads
- Integrated with Lambda for event-driven processing
- Cost-effective for large file storage

### 3. DynamoDB for Metadata

**Rationale:**
- NoSQL flexible schema for evolving metadata requirements
- Single-digit millisecond latency
- Built-in support for secondary indexes (filtering)
- Automatic scaling
- Strong consistency options

### 4. Separation of Concerns

**Images vs Metadata:**
- S3 stores binary image data (optimized for large objects)
- DynamoDB stores metadata (optimized for fast queries)
- Reduces database size and improves query performance
- Enables independent scaling of storage and database

## Data Models

### Image Metadata Schema (DynamoDB)

```python
{
    "image_id": "uuid-v4",              # Partition Key
    "user_id": "string",                # GSI Partition Key
    "filename": "string",
    "content_type": "string",           # image/jpeg, image/png, etc.
    "size": number,                     # bytes
    "s3_key": "string",                 # S3 object key
    "s3_bucket": "string",              # S3 bucket name
    "upload_timestamp": "string",       # ISO 8601 format
    "tags": ["string"],                 # Array of tags
    "description": "string",            # Optional description
    "width": number,                    # Image dimensions
    "height": number,
    "status": "string",                 # active, deleted
    "metadata": {                       # Additional custom metadata
        "location": "string",
        "camera": "string",
        ...
    }
}
```

### DynamoDB Table Design

**Table Name**: `images`

**Primary Key:**
- Partition Key: `image_id` (String)

**Global Secondary Indexes (GSI):**

1. **UserIndex**
   - Partition Key: `user_id`
   - Sort Key: `upload_timestamp`
   - Purpose: List all images by user, sorted by upload time

2. **StatusIndex**
   - Partition Key: `status`
   - Sort Key: `upload_timestamp`
   - Purpose: Filter by status (active/deleted)

**Attributes for Filtering:**
- `tags` - Array attribute for tag-based search
- `content_type` - Filter by image type
- `upload_timestamp` - Date range filtering

## API Design

### REST Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/images` | Upload image with metadata |
| GET | `/images` | List images with filters |
| GET | `/images/{image_id}` | Get image metadata |
| GET | `/images/{image_id}/download` | Download/view image |
| DELETE | `/images/{image_id}` | Delete image |

### API Specifications

#### 1. Upload Image

**Endpoint:** `POST /images`

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `image`: File (required)
  - `user_id`: String (required)
  - `description`: String (optional)
  - `tags`: JSON array (optional)
  - `metadata`: JSON object (optional)

**Response:** `201 Created`
```json
{
    "image_id": "uuid",
    "upload_url": "presigned-url",
    "message": "Image uploaded successfully"
}
```

#### 2. List Images

**Endpoint:** `GET /images`

**Query Parameters:**
- `user_id`: Filter by user (optional)
- `tags`: Comma-separated tags (optional)
- `content_type`: Filter by type (optional)
- `start_date`: ISO 8601 date (optional)
- `end_date`: ISO 8601 date (optional)
- `limit`: Number (default: 50, max: 100)
- `last_key`: Pagination token (optional)

**Response:** `200 OK`
```json
{
    "images": [
        {
            "image_id": "uuid",
            "filename": "photo.jpg",
            "upload_timestamp": "2025-12-27T10:30:00Z",
            "tags": ["nature", "landscape"],
            "size": 2048576,
            ...
        }
    ],
    "count": 10,
    "last_evaluated_key": "pagination-token"
}
```

#### 3. Get Image Metadata

**Endpoint:** `GET /images/{image_id}`

**Response:** `200 OK`
```json
{
    "image_id": "uuid",
    "filename": "photo.jpg",
    "content_type": "image/jpeg",
    "size": 2048576,
    "upload_timestamp": "2025-12-27T10:30:00Z",
    "tags": ["nature"],
    "description": "Beautiful sunset",
    "width": 1920,
    "height": 1080
}
```

#### 4. Download Image

**Endpoint:** `GET /images/{image_id}/download`

**Response:** `200 OK`
- Returns presigned S3 URL or redirects to S3
- Headers: Content-Type, Content-Disposition

#### 5. Delete Image

**Endpoint:** `DELETE /images/{image_id}`

**Response:** `204 No Content`

## Security Considerations

### 1. Authentication & Authorization
- API Gateway with AWS IAM or Cognito
- User-specific access control
- Validate user ownership before delete operations

### 2. Input Validation
- File type validation (whitelist: jpeg, png, gif, webp)
- File size limits (max: 10MB)
- Sanitize metadata inputs
- Prevent injection attacks

### 3. S3 Security
- Private bucket with no public access
- Presigned URLs with expiration (15 minutes)
- Server-side encryption (SSE-S3)
- Versioning enabled for recovery

### 4. Rate Limiting
- API Gateway throttling limits
- Per-user request quotas
- DDoS protection via AWS Shield

## Scalability Strategy

### Horizontal Scaling
- **Lambda**: Automatic concurrent execution scaling
- **DynamoDB**: On-demand capacity mode or auto-scaling
- **S3**: Unlimited storage capacity

### Performance Optimization
1. **Caching**: CloudFront CDN for frequently accessed images
2. **Lazy Loading**: Return metadata first, load images on-demand
3. **Pagination**: Limit query results, use cursor-based pagination
4. **Connection Pooling**: Reuse DynamoDB/S3 connections in Lambda
5. **Image Optimization**: Consider Lambda for thumbnail generation

### Monitoring & Observability
- CloudWatch Logs for Lambda execution
- X-Ray for distributed tracing
- Custom metrics for upload/download rates
- Alarms for error rates and latency

## Error Handling

### Error Response Format
```json
{
    "error": "ErrorCode",
    "message": "Human-readable error description",
    "request_id": "uuid"
}
```

### HTTP Status Codes
- `200 OK`: Successful GET/PUT
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Invalid input
- `404 Not Found`: Resource not found
- `413 Payload Too Large`: File size exceeded
- `415 Unsupported Media Type`: Invalid file type
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: Temporary unavailability

## Testing Strategy

### Unit Tests
- Lambda function logic (mocked AWS services)
- Validation functions
- Helper utilities
- Data transformations

### Integration Tests
- End-to-end API workflows
- DynamoDB operations
- S3 operations
- Error scenarios

### Test Coverage Goals
- Code coverage: >80%
- Branch coverage: >75%
- All API endpoints covered
- All error paths tested

### Testing Tools
- `pytest`: Test framework
- `moto`: AWS service mocking
- `pytest-cov`: Coverage reporting
- `LocalStack`: Local integration testing

## LocalStack Development Environment

### Services Used
- API Gateway (port 4566)
- Lambda (port 4566)
- S3 (port 4566)
- DynamoDB (port 4566)

### Starting LocalStack

LocalStack can be started using the LocalStack CLI (recommended) or Docker:

**Using LocalStack CLI (Recommended):**
```bash
# Start LocalStack with specific services
localstack start -d

# Check status
localstack status services

# View logs
localstack logs
```

**Using Docker directly:**
```bash
docker run --rm -it -d \
  --name localstack-main \
  -p 4566:4566 \
  -p 4510-4559:4510-4559 \
  -e SERVICES=apigateway,lambda,s3,dynamodb \
  -e DEBUG=1 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  localstack/localstack
```

**Configuration via Environment Variables:**
```bash
# Set before starting LocalStack
export SERVICES=apigateway,lambda,s3,dynamodb
export DEBUG=1
export LAMBDA_EXECUTOR=docker
```

## Deployment Strategy

### Development
1. LocalStack for local testing
2. Unit tests with moto
3. Integration tests with LocalStack

### Staging
1. AWS account with separate resources
2. CI/CD pipeline (GitHub Actions/GitLab CI)
3. Automated testing before deployment

### Production
1. Infrastructure as Code (AWS SAM or Terraform)
2. Blue-green deployment
3. Canary releases for gradual rollout
4. Automated rollback on errors

## Future Enhancements

1. **Image Processing**
   - Automatic thumbnail generation
   - Multiple size variants
   - Format conversion (WebP optimization)

2. **Advanced Search**
   - Full-text search with Elasticsearch
   - Image recognition with AWS Rekognition
   - Facial recognition and tagging

3. **Social Features**
   - Likes and comments
   - Image sharing
   - User feeds and timelines

4. **Analytics**
   - View counts
   - Popular images
   - User engagement metrics

5. **CDN Integration**
   - CloudFront distribution
   - Edge caching
   - Geographic optimization

## Constraints & Limitations

### AWS Lambda
- Max execution time: 15 minutes
- Max payload: 6MB (synchronous), 256KB (async)
- Max deployment package: 50MB (zipped), 250MB (unzipped)

### API Gateway
- Max payload: 10MB
- Timeout: 29 seconds

### Solutions
- Use presigned URLs for large file uploads (bypass Lambda limits)
- Implement async processing for long operations
- Stream large responses through S3

## Conclusion

This design provides a scalable, maintainable, and cost-effective solution for an Instagram-like image service. The serverless architecture ensures automatic scaling, while the separation of concerns between S3 and DynamoDB optimizes for both storage and query performance. The use of LocalStack enables efficient local development and testing without incurring AWS costs.
