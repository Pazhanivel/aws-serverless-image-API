# Development Setup Guide

## LocalStack Development Environment for AWS Serverless Image API

This guide will walk you through setting up a complete local development environment using LocalStack to emulate AWS services.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [AWS CLI Configuration](#aws-cli-configuration)
4. [LocalStack Setup](#localstack-setup)
5. [Resource Creation](#resource-creation)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.7+ | Backend development |
| LocalStack CLI | 3.x | LocalStack management |
| Docker | 20.x+ | Running LocalStack |
| Git | 2.x | Version control |

### Installation

```cmd
REM Install Python dependencies
pip install -r requirements.txt

REM This will install:
REM - boto3 (AWS SDK)
REM - localstack (LocalStack CLI)
REM - Other project dependencies
```

---

## Quick Start

**Get up and running in 5 minutes:**

### 1. Start LocalStack

```cmd
cd c:\Users\parumug\test\mPyCloud\aws-serverless-image-API
scripts\start_localstack.bat
```

### 2. Create Resources

```cmd
python scripts\create_resources.py
```

### 3. Verify Setup

```cmd
python scripts\verify_resources.py
```

## Detailed Setupbash
# 1. Clone the repository
git clone <repository-url>
cd mPyCloud

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start LocalStack (choose one method):
# Option A - LocalStack CLI (recommended):
localstack start -d

# Option B - Direct Docker:
docker run --rm -it -d -p 4566:4566 -p 4510-4559:4510-4559 -v /var/run/docker.sock:/var/run/docker.sock localstack/localstack

# 5. Create AWS resources
python scripts/create_resources.py

# 6. Run tests
pytest tests/

# 7. Deploy Lambda functions (optional)
python scripts/deploy.py
```

---

## Detailed Setup

### Step 1: Install Python 3.7+

**Windows:**
```powershell
# Download from python.org or use Chocolatey
choco install python --version=3.11.0

# Verify installation
python --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**macOS:**
```bash
brew install python@3.11
```

---

### Step 2: Install Docker Desktop

**Windows/macOS:**
1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
2. Install and start Docker Desktop
3. Verify installation:
```powershell
docker --version
```

**Linux:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Verify
docker --version
```

---

### Step 3: Install LocalStack CLI (Recommended)

The LocalStack CLI is the recommended way to manage LocalStack.

**Windows:**
```powershell
# Download binary from GitHub releases
# https://github.com/localstack/localstack-cli/releases/latest

# Or use Python (cross-platform):
python -m pip install localstack

# Verify
localstack --version
```

**macOS/Linux (Homebrew):**
```bash
brew install localstack/tap/localstack-cli

# Verify
localstack --version
```

**Linux (Binary):**
```bash
# x86-64
curl --output localstack-cli-4.12.0-linux-amd64-onefile.tar.gz \
  --location https://github.com/localstack/localstack-cli/releases/download/v4.12.0/localstack-cli-4.12.0-linux-amd64-onefile.tar.gz
sudo tar xvzf localstack-cli-4.12.0-linux-*-onefile.tar.gz -C /usr/local/bin
```

---

### Step 4: Install AWS CLI

**Windows:**
```powershell
# Download and install MSI from AWS
# Or use Chocolatey
choco install awscli

# Verify
aws --version
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**macOS:**
```bash
brew install awscli
```

---

### Step 5: Setup Project

```powershell
# Create project directory
mkdir mPyCloud
cd mPyCloud

# Initialize Git repository
git init

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Create requirements files
# (See requirements.txt section below)
```

---

## LocalStack Configuration

### Starting LocalStack

LocalStack offers multiple ways to start. Choose the method that works best for you:

#### Method 1: LocalStack CLI (Recommended)

The simplest and recommended way:

```powershell
# Start LocalStack in background
localstack start -d

# Check status
localstack status services

# View logs
localstack logs

# Stop LocalStack
localstack stop
```

**Configuration:** LocalStack CLI reads configuration from environment variables or a `.localstack` config file.

#### Method 2: Docker CLI

Direct Docker command for more control:

```powershell
# Start LocalStack container
docker run --rm -it -d \
  --name localstack-main \
  -p 127.0.0.1:4566:4566 \
  -p 127.0.0.1:4510-4559:4510-4559 \
  -e SERVICES=apigateway,lambda,s3,dynamodb,iam,sts,logs \
  -e DEBUG=1 \
  -e LAMBDA_EXECUTOR=docker \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "${PWD}/localstack-data:/var/lib/localstack" \
  localstack/localstack

# Check container status
docker ps

# View logs
docker logs localstack-main -f

# Stop container
docker stop localstack-main
```

### Verify LocalStack is Running

```powershell
# Check health endpoint
curl http://localhost:4566/_localstack/health

# Expected output:
{
  "services": {
    "apigateway": "running",
    "dynamodb": "running",
    "lambda": "running",
    "s3": "running",
    ...
  }
}
```

---

## AWS CLI Setup

### Option 1: Using awslocal (Recommended)

The **awslocal** wrapper automatically configures AWS CLI to use LocalStack:

```powershell
# Install awslocal
pip install awscli-local

# Use awslocal instead of aws - no endpoint configuration needed!
awslocal s3 ls
awslocal s3 mb s3://my-bucket
awslocal dynamodb list-tables
awslocal lambda list-functions
```

**Benefits:**
- Automatically uses `http://localhost:4566` endpoint
- No need to configure credentials
- No need to specify `--endpoint-url` every time
- Drop-in replacement for `aws` command

### Option 2: Using Standard AWS CLI

You can use the standard AWS CLI by specifying the endpoint:

**Method A - Using --endpoint-url flag:**
```powershell
# Specify endpoint for each command
aws --endpoint-url=http://localhost:4566 s3 ls
aws --endpoint-url=http://localhost:4566 s3 mb s3://my-bucket
aws --endpoint-url=http://localhost:4566 dynamodb list-tables
```

**Method B - Configure AWS profile for LocalStack:**
```powershell
# Create LocalStack profile
aws configure --profile localstack

# Enter the following:
# AWS Access Key ID: test
# AWS Secret Access Key: test
# Default region name: us-east-1
# Default output format: json

# Use the profile with endpoint URL
aws --profile localstack --endpoint-url=http://localhost:4566 s3 ls
```

**Method C - Set environment variables:**

**Windows (PowerShell):**
```powershell
# Add to your PowerShell profile or .env file
$env:AWS_ACCESS_KEY_ID="test"
$env:AWS_SECRET_ACCESS_KEY="test"
$env:AWS_DEFAULT_REGION="us-east-1"
$env:AWS_ENDPOINT_URL="http://localhost:4566"

# Now you can use aws without --endpoint-url
aws s3 ls
```

**Linux/macOS (Bash):**
```bash
# Add to ~/.bashrc or ~/.zshrc
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ENDPOINT_URL="http://localhost:4566"

# Now you can use aws without --endpoint-url
aws s3 ls
```

### Testing AWS CLI Configuration

```powershell
# Using awslocal
awslocal s3 ls
awslocal dynamodb list-tables

# Using standard AWS CLI
aws --endpoint-url=http://localhost:4566 s3 ls

# Check LocalStack services
curl http://localhost:4566/_localstack/health
```

---

## Resource Creation

### Create Setup Script

Create `scripts/create_resources.py`:

```python
#!/usr/bin/env python3
"""
Create AWS resources in LocalStack for mPyCloud
"""
import boto3
import json
import os

# LocalStack configuration
LOCALSTACK_ENDPOINT = os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566')
REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

# Resource names
S3_BUCKET_NAME = 'image-storage-bucket'
DYNAMODB_TABLE_NAME = 'images'

def get_client(service):
    """Get boto3 client configured for LocalStack"""
    return boto3.client(
        service,
        endpoint_url=LOCALSTACK_ENDPOINT,
        region_name=REGION,
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )

def create_s3_bucket():
    """Create S3 bucket for image storage"""
    print(f"Creating S3 bucket: {S3_BUCKET_NAME}")
    s3 = get_client('s3')
    
    try:
        s3.create_bucket(Bucket=S3_BUCKET_NAME)
        print(f"✓ S3 bucket '{S3_BUCKET_NAME}' created successfully")
        
        # Enable versioning (optional)
        s3.put_bucket_versioning(
            Bucket=S3_BUCKET_NAME,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print(f"✓ Versioning enabled on '{S3_BUCKET_NAME}'")
        
        # Block public access
        s3.put_public_access_block(
            Bucket=S3_BUCKET_NAME,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        print(f"✓ Public access blocked on '{S3_BUCKET_NAME}'")
        
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"⚠ S3 bucket '{S3_BUCKET_NAME}' already exists")
    except Exception as e:
        print(f"✗ Error creating S3 bucket: {e}")
        raise

def create_dynamodb_table():
    """Create DynamoDB table for image metadata"""
    print(f"Creating DynamoDB table: {DYNAMODB_TABLE_NAME}")
    dynamodb = get_client('dynamodb')
    
    try:
        dynamodb.create_table(
            TableName=DYNAMODB_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'image_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'image_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'upload_timestamp',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'upload_timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'status',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'upload_timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        # Wait for table to be active
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=DYNAMODB_TABLE_NAME)
        
        print(f"✓ DynamoDB table '{DYNAMODB_TABLE_NAME}' created successfully")
        
        # Describe table
        response = dynamodb.describe_table(TableName=DYNAMODB_TABLE_NAME)
        print(f"✓ Table Status: {response['Table']['TableStatus']}")
        print(f"✓ Global Secondary Indexes: {len(response['Table']['GlobalSecondaryIndexes'])}")
        
    except dynamodb.exceptions.ResourceInUseException:
        print(f"⚠ DynamoDB table '{DYNAMODB_TABLE_NAME}' already exists")
    except Exception as e:
        print(f"✗ Error creating DynamoDB table: {e}")
        raise

def verify_resources():
    """Verify all resources were created successfully"""
    print("\nVerifying resources...")
    
    # Verify S3
    s3 = get_client('s3')
    buckets = s3.list_buckets()
    bucket_names = [b['Name'] for b in buckets['Buckets']]
    
    if S3_BUCKET_NAME in bucket_names:
        print(f"✓ S3 bucket '{S3_BUCKET_NAME}' exists")
    else:
        print(f"✗ S3 bucket '{S3_BUCKET_NAME}' not found")
    
    # Verify DynamoDB
    dynamodb = get_client('dynamodb')
    tables = dynamodb.list_tables()
    
    if DYNAMODB_TABLE_NAME in tables['TableNames']:
        print(f"✓ DynamoDB table '{DYNAMODB_TABLE_NAME}' exists")
    else:
        print(f"✗ DynamoDB table '{DYNAMODB_TABLE_NAME}' not found")

def main():
    """Main setup function"""
    print("=" * 60)
    print("mPyCloud LocalStack Resource Setup")
    print("=" * 60)
    print()
    
    try:
        create_s3_bucket()
        print()
        create_dynamodb_table()
        print()
        verify_resources()
        
        print()
        print("=" * 60)
        print("✓ All resources created successfully!")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Setup failed: {e}")
        print("=" * 60)
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
```

### Run Resource Creation

```powershell
# Make script executable (Linux/Mac)
chmod +x scripts/create_resources.py

# Run script
python scripts/create_resources.py
```

### Manual Resource Creation (Alternative)

**Using AWS CLI:**

```powershell
# Create S3 bucket
aws --endpoint-url=http://localhost:4566 s3 mb s3://image-storage-bucket

# Create DynamoDB table
aws --endpoint-url=http://localhost:4566 dynamodb create-table \
    --table-name images \
    --attribute-definitions \
        AttributeName=image_id,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
        AttributeName=upload_timestamp,AttributeType=S \
        AttributeName=status,AttributeType=S \
    --key-schema AttributeName=image_id,KeyType=HASH \
    --global-secondary-indexes \
        "[{\"IndexName\": \"UserIndex\", \"KeySchema\": [{\"AttributeName\":\"user_id\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"upload_timestamp\",\"KeyType\":\"RANGE\"}], \"Projection\":{\"ProjectionType\":\"ALL\"}, \"ProvisionedThroughput\": {\"ReadCapacityUnits\": 5, \"WriteCapacityUnits\": 5}},{\"IndexName\": \"StatusIndex\", \"KeySchema\": [{\"AttributeName\":\"status\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"upload_timestamp\",\"KeyType\":\"RANGE\"}], \"Projection\":{\"ProjectionType\":\"ALL\"}, \"ProvisionedThroughput\": {\"ReadCapacityUnits\": 5, \"WriteCapacityUnits\": 5}}]" \
    --billing-mode PROVISIONED \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

---

## Testing the Setup

### Test S3

```python
# test_s3.py
import boto3

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:4566',
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name='us-east-1'
)

# List buckets
buckets = s3.list_buckets()
print("Buckets:", [b['Name'] for b in buckets['Buckets']])

# Upload test file
s3.put_object(
    Bucket='image-storage-bucket',
    Key='test.txt',
    Body=b'Hello LocalStack!'
)
print("✓ File uploaded")

# List objects
objects = s3.list_objects_v2(Bucket='image-storage-bucket')
print("Objects:", [o['Key'] for o in objects.get('Contents', [])])
```

### Test DynamoDB

```python
# test_dynamodb.py
import boto3
from datetime import datetime

dynamodb = boto3.client(
    'dynamodb',
    endpoint_url='http://localhost:4566',
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name='us-east-1'
)

# Put item
dynamodb.put_item(
    TableName='images',
    Item={
        'image_id': {'S': 'test-123'},
        'user_id': {'S': 'user123'},
        'filename': {'S': 'test.jpg'},
        'upload_timestamp': {'S': datetime.utcnow().isoformat()},
        'status': {'S': 'active'}
    }
)
print("✓ Item inserted")

# Get item
response = dynamodb.get_item(
    TableName='images',
    Key={'image_id': {'S': 'test-123'}}
)
print("Item:", response['Item'])

# Query by user_id
response = dynamodb.query(
    TableName='images',
    IndexName='UserIndex',
    KeyConditionExpression='user_id = :uid',
    ExpressionAttributeValues={':uid': {'S': 'user123'}}
)
print("Query results:", response['Count'], "items")
```

---

## Troubleshooting

### Common Issues

#### 1. LocalStack not starting

**Problem**: Container exits immediately

**Solution**:
```powershell
# Check Docker is running
docker ps

# Check LocalStack logs
localstack logs

# Check status
localstack status

# Restart LocalStack
localstack stop
localstack start -d
```

#### 2. Port 4566 already in use

**Problem**: Another service using port 4566

**Solution**:
```powershell
# Find process using port (Windows)
netstat -ano | findstr :4566

# Kill process
taskkill /PID <PID> /F

# Or stop LocalStack and use different configuration
localstack stop
# Set EDGE_PORT environment variable before starting
$env:EDGE_PORT="4567"
localstack start -d
```

#### 3. AWS CLI not connecting

**Problem**: Connection refused or timeout

**Solution**:
```powershell
# Verify LocalStack is running
curl http://localhost:4566/_localstack/health

# Check endpoint URL
echo $env:AWS_ENDPOINT_URL

# Use --endpoint-url explicitly
aws --endpoint-url=http://localhost:4566 s3 ls
```

#### 4. Lambda execution fails

**Problem**: Lambda timeout or error

**Solution**:
```powershell
# Check Lambda executor (if using Docker method)
docker exec localstack-main env | grep LAMBDA_EXECUTOR

# Check Docker socket mounted
docker exec localstack-main ls -l /var/run/docker.sock

# Set Lambda configuration via environment
$env:LAMBDA_EXECUTOR="docker"
localstack restart
```

#### 5. Permission denied errors

**Problem**: Can't access files or Docker socket

**Solution (Linux)**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Fix permissions on localstack-data
sudo chown -R $USER:$USER localstack-data/
```

### Debug Mode

Enable detailed logging:

```powershell
# Set environment variables before starting
$env:DEBUG="1"
$env:LS_LOG="trace"
$env:LAMBDA_DOCKER_FLAGS="-e DEBUG=1"

localstack start -d
```

### Reset LocalStack

Complete clean slate:

```powershell
# Stop and remove everything
docker-compose down -v

# Remove data directory
Remove-Item -Recurse -Force localstack-data

# Start fresh
docker-compose up -d

# Recreate resources
python scripts/create_resources.py
```

---

## Development Workflow

### Daily Workflow

```powershell
# 1. Start LocalStack
docker-compose up -d

# 2. Activate Python environment
venv\Scripts\activate

# 3. Verify resources exist
python scripts/create_resources.py

# 4. Run development server or tests
pytest tests/

# 5. Make changes to code

# 6. Test changes
pytest tests/integration/

# 7. When done, stop LocalStack
docker-compose down
```

### Testing Workflow

```powershell
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_s3_service.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run integration tests only
pytest tests/integration/

# Run with verbose output
pytest -v

# Run and watch for changes
pytest-watch
```

### Deployment Workflow

```powershell
# 1. Create Lambda deployment packages
python scripts/package_lambda.py

# 2. Deploy to LocalStack
python scripts/deploy.py

# 3. Test deployed endpoints
curl http://localhost:4566/restapis/{api-id}/dev/_user_request_/images

# 4. View logs
docker-compose logs -f localstack | grep lambda
```

---

## Environment Variables

Create `.env` file (don't commit to Git):

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
AWS_ENDPOINT_URL=http://localhost:4566

# LocalStack Configuration
LOCALSTACK_HOSTNAME=localhost
EDGE_PORT=4566

# Application Configuration
S3_BUCKET_NAME=image-storage-bucket
DYNAMODB_TABLE_NAME=images
MAX_FILE_SIZE=10485760
ALLOWED_CONTENT_TYPES=image/jpeg,image/png,image/gif,image/webp

# Development
DEBUG=True
LOG_LEVEL=DEBUG
```

Load environment variables:

```powershell
# Windows PowerShell
Get-Content .env | ForEach-Object {
    $name, $value = $_.split('=')
    Set-Content env:\$name $value
}

# Linux/Mac
export $(cat .env | xargs)
```

---

## Next Steps

After completing the setup:

1. ✅ **Verify** all resources are created
2. ✅ **Run** test scripts to validate connectivity
3. ✅ **Implement** Lambda functions (see IMPLEMENTATION_PLAN.md)
4. ✅ **Write** unit tests
5. ✅ **Deploy** to LocalStack
6. ✅ **Test** API endpoints
7. ✅ **Document** any issues or customizations

---

### Additional Resources

### LocalStack Documentation
- [Official Documentation](https://docs.localstack.cloud/)
- [Installation Guide](https://docs.localstack.cloud/getting-started/installation/)
- [GitHub Repository](https://github.com/localstack/localstack)
- [AWS Service Coverage](https://docs.localstack.cloud/references/coverage/)
- [LocalStack CLI Documentation](https://docs.localstack.cloud/getting-started/installation/#localstack-cli)
- [AWS CLI Integration](https://docs.localstack.cloud/user-guide/integrations/aws-cli/)

### Boto3 Documentation
- [Boto3 Docs](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [S3 Examples](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-examples.html)
- [DynamoDB Examples](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html)

### AWS Lambda
- [Lambda Handler in Python](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html)
- [Lambda Environment Variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)

### Testing
- [pytest Documentation](https://docs.pytest.org/)
- [moto (AWS mocking)](https://github.com/getmoto/moto)

---

**Last Updated**: December 27, 2025  
**Maintained By**: Development Team
