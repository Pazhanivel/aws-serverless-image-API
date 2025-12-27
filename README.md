# mPyCloud - Instagram-like Image Service

A scalable, serverless image management service built with AWS Lambda, S3, DynamoDB, and API Gateway. Designed for handling image uploads, storage, retrieval, and management with support for metadata and advanced filtering.

## 🚀 Features

- ✅ **Image Upload** - Upload images with metadata (tags, description, custom fields)
- ✅ **Smart Search** - Filter by user, tags, content type, and date range
- ✅ **Secure Download** - Presigned URLs for secure image access
- ✅ **Image Management** - View metadata and delete images
- ✅ **Scalable Architecture** - Serverless design with AWS Lambda
- ✅ **Local Development** - LocalStack for offline development
- ✅ **Comprehensive Testing** - Unit and integration tests
- ✅ **API Documentation** - Complete REST API documentation

## 📋 Requirements

- Python 3.7+
- Docker (20.x+)
- AWS CLI v2
- LocalStack CLI (recommended) or LocalStack Docker image

## 🏗️ Architecture

```
Client → API Gateway → Lambda Functions → S3 (Images) + DynamoDB (Metadata)
```

### Technology Stack

- **API Layer**: AWS API Gateway
- **Compute**: AWS Lambda (Python 3.7+)
- **Storage**: Amazon S3
- **Database**: Amazon DynamoDB
- **Local Dev**: LocalStack
- **Testing**: pytest, moto

## 📁 Project Structure

```
mPyCloud/
├── src/                          # Source code
│   ├── handlers/                 # Lambda function handlers
│   │   ├── __init__.py
│   │   ├── upload_handler.py     # POST /images
│   │   ├── list_handler.py       # GET /images
│   │   ├── get_handler.py        # GET /images/{id}
│   │   ├── download_handler.py   # GET /images/{id}/download
│   │   └── delete_handler.py     # DELETE /images/{id}
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── s3_service.py         # S3 operations
│   │   ├── dynamodb_service.py   # DynamoDB operations
│   │   └── image_service.py      # Image processing & orchestration
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   └── image_metadata.py     # ImageMetadata class
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── validators.py         # Input validation
│   │   ├── response.py           # API response formatting
│   │   └── logger.py             # Logging utilities
│   └── config/                   # Configuration
│       ├── __init__.py
│       └── settings.py           # Environment settings
│
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   │   ├── test_validators.py
│   │   ├── test_image_metadata.py
│   │   ├── test_s3_service.py
│   │   ├── test_dynamodb_service.py
│   │   ├── test_image_service.py
│   │   ├── test_upload_handler.py
│   │   ├── test_list_handler.py
│   │   ├── test_get_handler.py
│   │   ├── test_download_handler.py
│   │   └── test_delete_handler.py
│   ├── integration/              # Integration tests
│   │   ├── test_upload_workflow.py
│   │   ├── test_list_workflow.py
│   │   ├── test_download_workflow.py
│   │   └── test_delete_workflow.py
│   └── fixtures/                 # Test data
│       └── sample_images/
│
├── scripts/                      # Utility scripts
│   ├── create_resources.py       # Setup AWS resources in LocalStack
│   ├── deploy.py                 # Deploy Lambda functions
│   ├── cleanup.sh                # Cleanup resources
│   └── package_lambda.py         # Package Lambda deployment
│
├── docs/                         # Documentation
│   ├── API.md                    # API documentation
│   ├── SETUP.md                  # Setup guide
│   └── ARCHITECTURE.md           # Architecture details
│
├── template.yaml                 # AWS SAM template
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Development dependencies
├── pytest.ini                    # pytest configuration
├── .gitignore                    # Git ignore rules
├── .env.example                  # Environment variables template
├── README.md                     # This file
├── DESIGN.md                     # Design document
└── IMPLEMENTATION_PLAN.md        # Implementation plan
```

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd mPyCloud
```

### 2. Setup Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Start LocalStack

```bash
# Install LocalStack CLI (if not already installed)
pip install localstack

# Start LocalStack in background
localstack start -d

# Verify it's running
curl http://localhost:4566/_localstack/health

# Or check service status
localstack status services
```

### 4. Create AWS Resources

```bash
# Create S3 bucket and DynamoDB table
python scripts/create_resources.py
```

### 5. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_upload_handler.py
```

### 6. Deploy (Optional)

```bash
# Deploy Lambda functions to LocalStack
python scripts/deploy.py
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[API Documentation](docs/API.md)** - Complete API reference with examples
- **[Setup Guide](docs/SETUP.md)** - Detailed setup instructions
- **[Design Document](DESIGN.md)** - Architecture and design decisions
- **[Implementation Plan](IMPLEMENTATION_PLAN.md)** - Development roadmap

## 🔧 Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
AWS_ENDPOINT_URL=http://localhost:4566

# Application Configuration
S3_BUCKET_NAME=image-storage-bucket
DYNAMODB_TABLE_NAME=images
MAX_FILE_SIZE=10485760
ALLOWED_CONTENT_TYPES=image/jpeg,image/png,image/gif,image/webp

# Development
DEBUG=True
LOG_LEVEL=DEBUG
```

### AWS Resources

The following resources are created in LocalStack:

| Resource | Name | Purpose |
|----------|------|---------|
| S3 Bucket | `image-storage-bucket` | Store uploaded images |
| DynamoDB Table | `images` | Store image metadata |
| GSI | `UserIndex` | Query by user_id |
| GSI | `StatusIndex` | Query by status |

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_upload_handler.py

# With verbose output
pytest -v

# With coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Test Coverage Goals

- Overall coverage: >80%
- Unit tests: >90%
- Integration tests: >70%

## 📡 API Endpoints

### Base URL

```
http://localhost:4566/dev
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/images` | Upload image with metadata |
| GET | `/images` | List images with filters |
| GET | `/images/{id}` | Get image metadata |
| GET | `/images/{id}/download` | Download image |
| DELETE | `/images/{id}` | Delete image |

### Example Usage

**Upload Image:**
```bash
curl -X POST http://localhost:4566/dev/images \
  -F "image=@photo.jpg" \
  -F "user_id=user123" \
  -F "description=My photo" \
  -F 'tags=["nature", "sunset"]'
```

**List Images:**
```bash
curl "http://localhost:4566/dev/images?user_id=user123&tags=nature"
```

**Get Image:**
```bash
curl http://localhost:4566/dev/images/{image_id}
```

**Download Image:**
```bash
curl http://localhost:4566/dev/images/{image_id}/download
```

**Delete Image:**
```bash
curl -X DELETE http://localhost:4566/dev/images/{image_id}
```

See [API Documentation](docs/API.md) for complete details.

## 🐍 Python Examples

```python
import requests

BASE_URL = "http://localhost:4566/dev"

# Upload image
with open('photo.jpg', 'rb') as f:
    files = {'image': f}
    data = {
        'user_id': 'user123',
        'description': 'My photo',
        'tags': '["nature", "sunset"]'
    }
    response = requests.post(f"{BASE_URL}/images", files=files, data=data)
    result = response.json()
    image_id = result['image_id']

# List images
response = requests.get(f"{BASE_URL}/images", params={'user_id': 'user123'})
images = response.json()

# Get metadata
response = requests.get(f"{BASE_URL}/images/{image_id}")
metadata = response.json()

# Download image
response = requests.get(f"{BASE_URL}/images/{image_id}/download")
download_url = response.json()['download_url']
image_data = requests.get(download_url).content

# Delete image
response = requests.delete(f"{BASE_URL}/images/{image_id}")
```

## 🛠️ Development

### Project Dependencies

**Core Dependencies:**
- `boto3` - AWS SDK for Python
- `python-multipart` - Multipart form data parsing
- `Pillow` - Image processing

**Development Dependencies:**
- `pytest` - Testing framework
- `pytest-cov` - Coverage plugin
- `moto` - AWS service mocking
- `black` - Code formatting
- `pylint` - Linting
- `mypy` - Type checking

### Code Standards

- Follow PEP 8 style guide
- Use type hints for function signatures
- Write docstrings for all public functions
- Maintain >80% test coverage
- Use meaningful variable names

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "Add feature: description"

# Push to remote
git push origin feature/your-feature

# Create pull request
```

## 🐛 Troubleshooting

### LocalStack not starting

```bash
# Check Docker is running
docker ps

# View LocalStack logs
localstack logs

# Check status
localstack status

# Restart LocalStack
localstack stop
localstack start -d
```

### Port 4566 already in use

```powershell
# Find and kill process (Windows)
netstat -ano | findstr :4566
taskkill /PID <PID> /F
```

### AWS CLI connection issues

```bash
# Verify endpoint
echo $AWS_ENDPOINT_URL

# Test connection
curl http://localhost:4566/_localstack/health

# Use explicit endpoint
aws --endpoint-url=http://localhost:4566 s3 ls
```

### Reset LocalStack

```bash
# Complete reset
localstack stop
rm -rf .localstack/  # Remove LocalStack data
localstack start -d
python scripts/create_resources.py
```

See [Setup Guide](docs/SETUP.md) for detailed troubleshooting.

## 📊 Project Status

### Completed ✅

- [x] Design document
- [x] Implementation plan
- [x] API documentation
- [x] Setup guide
- [x] Project structure

### In Progress 🚧

- [ ] Lambda handlers implementation
- [ ] Service layer implementation
- [ ] Unit tests
- [ ] Integration tests

### Planned 📋

- [ ] Performance optimization
- [ ] Authentication/Authorization
- [ ] Image thumbnail generation
- [ ] Batch operations
- [ ] CI/CD pipeline

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Ensure tests pass
6. Submit a pull request

## 📄 License

This project is created as a coding exercise and is available for educational purposes.

## 👥 Authors

- Development Team

## 🙏 Acknowledgments

- AWS for cloud services
- LocalStack for local development environment
- Python community for excellent tools and libraries

## 📞 Support

- **Documentation**: See `docs/` folder
- **Issues**: Create an issue in the repository
- **Questions**: Contact the development team

## 🔗 Useful Links

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [LocalStack Documentation](https://docs.localstack.cloud/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [pytest Documentation](https://docs.pytest.org/)

---

**Last Updated**: December 27, 2025  
**Version**: 1.0.0  
**Status**: Documentation Phase Complete
