# AWS Serverless Image API - Scripts

This folder contains Python scripts for managing LocalStack and AWS resources.

## Available Scripts

### Resource Management (Python)

- **create_resources.py** - Create S3 bucket and DynamoDB table
- **verify_resources.py** - Verify all resources are created correctly
- **cleanup_resources.py** - Delete all resources from LocalStack

### LocalStack Management (Docker)

- **start_localstack.bat** - Start LocalStack Docker container
- **stop_localstack.bat** - Stop and remove LocalStack container

## Usage

### First Time Setup

```cmd
REM 1. Start LocalStack
scripts\start_localstack.bat

REM 2. Create resources
python scripts\create_resources.py

REM 3. Verify setup
python scripts\verify_resources.py
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
- LocalStack CLI installed (`pip install localstack`)
- Docker Desktop running

## Environment Variables

All scripts support these environment variables:

- `LOCALSTACK_ENDPOINT` - Default: http://localhost:4566
- `AWS_DEFAULT_REGION` - Default: us-east-1
- `S3_BUCKET_NAME` - Default: image-storage-bucket
- `DYNAMODB_TABLE_NAME` - Default: images

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