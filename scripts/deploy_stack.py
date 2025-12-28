#!/usr/bin/env python3
"""
Deploy Lambda functions and API Gateway to LocalStack using SAM template.
"""

import os
import sys
import json
import zipfile
import tempfile
import shutil
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Configuration
LOCALSTACK_ENDPOINT = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
STACK_NAME = 'image-api-stack'
S3_BUCKET_NAME = 'image-storage-bucket'
DYNAMODB_TABLE_NAME = 'images'

# Initialize AWS clients
session = boto3.Session(
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name=AWS_REGION
)

lambda_client = session.client('lambda', endpoint_url=LOCALSTACK_ENDPOINT)
apigateway_client = session.client('apigateway', endpoint_url=LOCALSTACK_ENDPOINT)
s3_client = session.client('s3', endpoint_url=LOCALSTACK_ENDPOINT)
iam_client = session.client('iam', endpoint_url=LOCALSTACK_ENDPOINT)


def create_deployment_package():
    """Create a ZIP file with all Lambda code."""
    print("\n📦 Creating Lambda deployment package...")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, 'lambda_package.zip')
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add src directory
            src_dir = project_root / 'src'
            for root, dirs, files in os.walk(src_dir):
                # Skip __pycache__ and .pyc files
                dirs[:] = [d for d in dirs if d != '__pycache__']
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, project_root)
                        zipf.write(file_path, arcname)
                        
        print(f"✅ Deployment package created: {zip_path}")
        return zip_path
    except Exception as e:
        print(f"❌ Error creating deployment package: {str(e)}")
        shutil.rmtree(temp_dir)
        raise


def create_lambda_role():
    """Create IAM role for Lambda functions."""
    print("\n🔑 Creating Lambda execution role...")
    
    role_name = 'lambda-execution-role'
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            Description='Execution role for image API Lambda functions'
        )
        role_arn = response['Role']['Arn']
        print(f"✅ Role created: {role_arn}")
        
        # Attach policies
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AmazonS3FullAccess',
            'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'
        ]
        
        for policy_arn in policies:
            try:
                iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
            except:
                pass  # Policies might not exist in LocalStack
                
        return role_arn
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            response = iam_client.get_role(RoleName=role_name)
            print(f"✅ Using existing role: {response['Role']['Arn']}")
            return response['Role']['Arn']
        raise


def create_lambda_function(name, handler, description, zip_path, role_arn):
    """Create a Lambda function."""
    print(f"\n🚀 Creating Lambda function: {name}")
    
    function_name = f'image-api-{name}'
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    environment_vars = {
        'LOCALSTACK_ENDPOINT': 'http://host.docker.internal:4566',  # LocalStack from inside container
        'AWS_DEFAULT_REGION': AWS_REGION,
        'S3_BUCKET_NAME': S3_BUCKET_NAME,
        'DYNAMODB_TABLE_NAME': DYNAMODB_TABLE_NAME,
        'USE_LOCALSTACK': 'true',
        'LOG_LEVEL': 'INFO',
        'MAX_IMAGE_SIZE': '10485760'
    }
    
    try:
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role=role_arn,
            Handler=handler,
            Code={'ZipFile': zip_content},
            Description=description,
            Timeout=30,
            MemorySize=512,
            Environment={'Variables': environment_vars}
        )
        print(f"✅ Lambda function created: {response['FunctionArn']}")
        return response['FunctionArn']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print(f"⚠️  Function already exists, updating code...")
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=role_arn,
                Handler=handler,
                Description=description,
                Timeout=30,
                MemorySize=512,
                Environment={'Variables': environment_vars}
            )
            print(f"✅ Lambda function updated: {response['FunctionArn']}")
            return response['FunctionArn']
        raise


def create_api_gateway(lambda_functions):
    """Create API Gateway with Lambda integrations."""
    print("\n🌐 Creating API Gateway...")
    
    api_name = 'image-api'
    
    # Check if API exists
    try:
        apis = apigateway_client.get_rest_apis()
        for api in apis.get('items', []):
            if api['name'] == api_name:
                print(f"⚠️  API already exists, deleting old version...")
                apigateway_client.delete_rest_api(restApiId=api['id'])
    except:
        pass
    
    # Create API
    api_response = apigateway_client.create_rest_api(
        name=api_name,
        description='Instagram-like Image Service API',
        endpointConfiguration={'types': ['REGIONAL']}
    )
    api_id = api_response['id']
    print(f"✅ API Gateway created: {api_id}")
    
    # Get root resource
    resources = apigateway_client.get_resources(restApiId=api_id)
    root_id = resources['items'][0]['id']
    
    # Create /images resource
    images_resource = apigateway_client.create_resource(
        restApiId=api_id,
        parentId=root_id,
        pathPart='images'
    )
    images_resource_id = images_resource['id']
    
    # Create /{image_id} resource
    image_id_resource = apigateway_client.create_resource(
        restApiId=api_id,
        parentId=images_resource_id,
        pathPart='{image_id}'
    )
    image_id_resource_id = image_id_resource['id']
    
    # Create /{image_id}/download resource
    download_resource = apigateway_client.create_resource(
        restApiId=api_id,
        parentId=image_id_resource_id,
        pathPart='download'
    )
    download_resource_id = download_resource['id']
    
    # Configure methods and integrations
    endpoints = [
        ('POST', images_resource_id, lambda_functions['upload'], '/images'),
        ('GET', images_resource_id, lambda_functions['list'], '/images'),
        ('GET', image_id_resource_id, lambda_functions['get'], '/images/{image_id}'),
        ('GET', download_resource_id, lambda_functions['download'], '/images/{image_id}/download'),
        ('DELETE', image_id_resource_id, lambda_functions['delete'], '/images/{image_id}'),
        ('PATCH', image_id_resource_id, lambda_functions['update_status'], '/images/{image_id}'),
    ]
    
    for method, resource_id, lambda_arn, path in endpoints:
        # Create method
        apigateway_client.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=method,
            authorizationType='NONE',
            requestParameters={
                'method.request.header.user-id': False,
                'method.request.header.User-Id': False
            }
        )
        
        # Create integration
        uri = f'arn:aws:apigateway:{AWS_REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        apigateway_client.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=method,
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=uri
        )
        
        print(f"✅ Configured {method} {path}")
    
    # Enable CORS for all resources
    for resource_id in [images_resource_id, image_id_resource_id, download_resource_id]:
        try:
            apigateway_client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            apigateway_client.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True,
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            )
            
            apigateway_client.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={'application/json': '{"statusCode": 200}'}
            )
            
            apigateway_client.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization,user-id,User-Id'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,DELETE,OPTIONS'",
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            )
        except:
            pass
    
    # Deploy API
    deployment = apigateway_client.create_deployment(
        restApiId=api_id,
        stageName='dev',
        description='Development stage'
    )
    
    api_url = f"{LOCALSTACK_ENDPOINT}/restapis/{api_id}/dev/_user_request_"
    print(f"\n✅ API deployed successfully!")
    print(f"📍 API URL: {api_url}")
    
    return api_id, api_url


def main():
    """Main deployment function."""
    print("=" * 60)
    print("🚀 Deploying Image API Stack to LocalStack")
    print("=" * 60)
    
    try:
        # Create deployment package
        zip_path = create_deployment_package()
        
        # Create IAM role
        role_arn = create_lambda_role()
        
        # Define Lambda functions
        functions = {
            'upload': {
                'handler': 'src.handlers.upload_handler.lambda_handler',
                'description': 'Generate presigned S3 URL for image upload'
            },
            'list': {
                'handler': 'src.handlers.list_handler.lambda_handler',
                'description': 'List images with filters and pagination'
            },
            'get': {
                'handler': 'src.handlers.get_handler.lambda_handler',
                'description': 'Get image metadata by ID'
            },
            'download': {
                'handler': 'src.handlers.download_handler.lambda_handler',
                'description': 'Generate presigned URL for image download'
            },
            'delete': {
                'handler': 'src.handlers.delete_handler.lambda_handler',
                'description': 'Delete image (soft or hard delete)'
            },
            'update_status': {
                'handler': 'src.handlers.update_status_handler.lambda_handler',
                'description': 'Update image status after S3 upload'
            }
        }
        
        # Create Lambda functions
        lambda_arns = {}
        for name, config in functions.items():
            lambda_arns[name] = create_lambda_function(
                name, config['handler'], config['description'], zip_path, role_arn
            )
        
        # Create API Gateway
        api_id, api_url = create_api_gateway(lambda_arns)
        
        # Clean up
        shutil.rmtree(os.path.dirname(zip_path))
        
        print("\n" + "=" * 60)
        print("✅ Deployment completed successfully!")
        print("=" * 60)
        print(f"\n📍 API Endpoint: {api_url}")
        print("\n📋 Available endpoints:")
        print(f"  POST   {api_url}/images")
        print(f"  GET    {api_url}/images")
        print(f"  GET    {api_url}/images/{{image_id}}")
        print(f"  PATCH  {api_url}/images/{{image_id}}")
        print(f"  GET    {api_url}/images/{{image_id}}/download")
        print(f"  DELETE {api_url}/images/{{image_id}}")
        print("\n💡 Test with: curl {api_url}/images")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
