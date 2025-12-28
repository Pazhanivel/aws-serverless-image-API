# AWS Serverless Image API - Scripts

This folder contains Python scripts for managing LocalStack and AWS resources.

## Available Scripts

### Resource Management (Python)

- **create_resources.py** - Create S3 bucket and DynamoDB table
- **deploy_stack.py** - Deploy Lambda functions and API Gateway
- **verify_resources.py** - Verify all resources are created correctly
- **cleanup_resources.py** - Delete all resources from LocalStack

### LocalStack Management (Docker)

- **start_localstack.bat** - Start LocalStack Docker container
- **stop_localstack.bat** - Stop and remove LocalStack container

## Usage

### First Time Setup

```cmd
REM 1. Start LocalStack (automatically creates resources and deploys stack)
scripts\start_localstack.bat

REM 2. Verify setup
python scripts\verify_resources.py
```

### Manual Deployment

If you need to redeploy the Lambda functions and API Gateway:

```cmd
REM Deploy/update stack
python scripts\deploy_stack.py
```

### Daily Development

```cmd
REM Verify resources before starting work
python scripts\verify_resources.py

REM Your development work here...
```

### Clean Up

```cmd
REM Remove all resources
python scripts\cleanup_resources.py

REM Stop LocalStack
scripts\stop_localstack.bat
```

## Prerequisites

- Python 3.7+ with boto3 installed (`pip install boto3`)
- Docker Desktop running
- Docker Compose (included with Docker Desktop)

## Environment Variables

All scripts support these environment variables:
## Resources Created

### S3 Bucket
- **Name**: image-storage-bucket
- **Purpose**: Store uploaded image files

### DynamoDB Table
- **Name**: images
- **Primary Key**: image_id (String)
- **GSIs**: 
  - UserIndex (user_id + upload_timestamp)
  - StatusIndex (status + upload_timestamp)

### Lambda Functions
- **image-api-upload** - Generate presigned S3 upload URLs
- **image-api-list** - List images with filtering and pagination
- **image-api-get** - Get image metadata by ID
- **image-api-download** - Generate presigned download URLs
- **image-api-delete** - Delete images (soft/hard)

### API Gateway
- **Name**: image-api
- **Stage**: dev
- **Endpoints**:
  - `POST /images` - Upload image (get presigned URL)
  - `GET /images` - List images
  - `GET /images/{image_id}` - Get image metadata
  - `GET /images/{image_id}/download` - Download image
  - `DELETE /images/{image_id}` - Delete image
### DynamoDB Table
- **Name**: images
- **Primary Key**: image_id (String)
- **GSIs**: 
  - UserIndex (user_id + upload_timestamp)
  - StatusIndex (status + upload_timestamp)