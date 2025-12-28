# Integration Tests

Comprehensive integration tests for the Image API endpoints.

## Prerequisites

1. **LocalStack Running**: Start LocalStack with deployed stack
   ```cmd
   scripts\start_localstack.bat
   ```

2. **Dependencies Installed**: Install test dependencies
   ```cmd
   pip install -r requirements-dev.txt
   ```

## Test Structure

```
tests/integration/
├── conftest.py              # Fixtures and utilities
├── test_upload.py           # Upload endpoint tests (10 tests)
├── test_list.py             # List endpoint tests (12 tests)
├── test_get.py              # Get metadata tests (9 tests)
├── test_download.py         # Download endpoint tests (12 tests)
├── test_delete.py           # Delete endpoint tests (11 tests)
└── test_e2e_workflows.py    # End-to-end workflows (6 tests)
```

**Total: 60 integration tests**

## Running Tests

### Run All Integration Tests
```cmd
pytest tests/integration -v
```

### Run Specific Test File
```cmd
pytest tests/integration/test_upload.py -v
pytest tests/integration/test_list.py -v
pytest tests/integration/test_download.py -v
```

### Run Specific Test
```cmd
pytest tests/integration/test_upload.py::TestUploadEndpoint::test_upload_successful_presigned_url_generation -v
```

### Run with Coverage
```cmd
pytest tests/integration --cov=src --cov-report=html
```

### Run E2E Workflows Only
```cmd
pytest tests/integration/test_e2e_workflows.py -v
```

## Test Coverage

### Upload Endpoint (`POST /images`)
- ✅ Successful presigned URL generation
- ✅ Full upload flow (presigned URL → S3 upload)
- ✅ Missing/invalid parameters validation
- ✅ Content type validation (JPEG, PNG, GIF)
- ✅ Tags and description support
- ✅ User authentication

### List Endpoint (`GET /images`)
- ✅ List all images
- ✅ Pagination with limit and next_token
- ✅ Filter by content type
- ✅ Filter by tags (single and multiple)
- ✅ Empty results handling
- ✅ Timestamp ordering (newest first)

### Get Endpoint (`GET /images/{image_id}`)
- ✅ Retrieve metadata by ID
- ✅ Tags and description retrieval
- ✅ Non-existent image handling
- ✅ Authorization (wrong user)
- ✅ Invalid ID format validation
- ✅ Metadata completeness

### Download Endpoint (`GET /images/{image_id}/download`)
- ✅ Presigned download URL generation
- ✅ Redirect mode (302)
- ✅ Actual file download verification
- ✅ Content type verification
- ✅ Multiple download attempts
- ✅ Custom expiration time
- ✅ Authorization checks

### Delete Endpoint (`DELETE /images/{image_id}`)
- ✅ Soft delete (status update)
- ✅ Hard delete (complete removal)
- ✅ S3 and DynamoDB cleanup verification
- ✅ Already deleted image handling
- ✅ Authorization checks
- ✅ Soft → Hard delete workflow

### E2E Workflows
- ✅ Complete workflow: Upload → Download → Delete
- ✅ Multiple images batch operations
- ✅ Tag-based search workflow
- ✅ Pagination workflow
- ✅ Error recovery
- ✅ Concurrent operations

## Fixtures

### Session-Scoped Fixtures
- `aws_credentials`: Mock AWS credentials for LocalStack
- `s3_client`: S3 client configured for LocalStack
- `dynamodb_client`: DynamoDB client for LocalStack
- `dynamodb_resource`: DynamoDB resource for LocalStack
- `api_gateway_client`: API Gateway client
- `api_base_url`: API Gateway base URL

### Function-Scoped Fixtures
- `test_user_id`: Test user ID
- `api_headers`: Default API headers with User-Id
- `sample_image_metadata`: Sample metadata for testing
- `sample_image_file`: 1x1 red pixel JPEG file
- `cleanup`: Cleanup fixture (runs after each test)

### Helper Functions
- `cleanup_test_images()`: Remove test data from DynamoDB and S3

## Test Data

All tests use:
- **User ID**: `test-user-123`
- **Sample Image**: Minimal 1x1 red pixel JPEG (valid JPEG format)
- **Content Types**: `image/jpeg`, `image/png`, `image/gif`
- **Tags**: Various test tags for filtering

## Cleanup

Tests automatically clean up after themselves using the `cleanup` fixture. To manually clean up all test data:

```cmd
python scripts/cleanup_resources.py
```

## Troubleshooting

### API Gateway Not Found
If you get "API Gateway not deployed" error:
```cmd
python scripts/deploy_stack.py
```

### LocalStack Not Running
```cmd
scripts\start_localstack.bat
```

### Connection Errors
Verify LocalStack is accessible:
```cmd
curl http://localhost:4566/_localstack/health
```

### Test Failures
1. Check LocalStack logs: `docker-compose logs -f localstack`
2. Verify resources: `python scripts/verify_resources.py`
3. Run tests with verbose output: `pytest -vv`

## CI/CD Integration

To run tests in CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Start LocalStack
  run: docker-compose up -d
  
- name: Wait for LocalStack
  run: sleep 10

- name: Setup resources
  run: |
    python scripts/create_resources.py
    python scripts/deploy_stack.py

- name: Run integration tests
  run: pytest tests/integration -v --cov=src
```

## Best Practices

1. **Test Isolation**: Each test creates its own data and cleans up
2. **Fixtures**: Use fixtures for common setup/teardown
3. **Real API Calls**: Tests make actual HTTP requests to LocalStack
4. **Assertions**: Comprehensive assertions for response structure and data
5. **Error Cases**: Tests cover both success and error scenarios
6. **Documentation**: Each test has clear docstring explaining its purpose

## Performance

Expected test execution time:
- All integration tests: ~30-60 seconds
- Single test file: ~5-10 seconds
- E2E workflows: ~10-15 seconds

Times may vary based on LocalStack startup and network conditions.
