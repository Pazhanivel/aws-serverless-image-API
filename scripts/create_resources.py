#!/usr/bin/env python3
"""
LocalStack Resource Creation Script

This script creates the necessary AWS resources in LocalStack:
- S3 bucket for image storage
- DynamoDB table for image metadata with GSIs

Usage:
    python create_resources.py
"""

import boto3
import os
import sys
from datetime import datetime


def create_s3_bucket(s3_client, bucket_name):
    """Create S3 bucket for image storage"""
    try:
        # For LocalStack, we can use us-east-1
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"✅ Created S3 bucket: {bucket_name}")
    except Exception as e:
        print(f"❌ Failed to create S3 bucket: {e}")
        return False
    return True


def create_dynamodb_table(dynamodb_client, table_name):
    """Create DynamoDB table with GSIs for image metadata"""
    try:
        table = dynamodb_client.create_table(
            TableName=table_name,
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
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'upload_timestamp',
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
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print(f"✅ Created DynamoDB table: {table_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to create DynamoDB table: {e}")
        return False


def verify_resources(s3_client, dynamodb_client, bucket_name, table_name):
    """Verify that resources were created successfully"""
    print("\n🔍 Verifying resources...")

    # Verify S3 bucket
    try:
        buckets = s3_client.list_buckets()
        bucket_names = [b['Name'] for b in buckets['Buckets']]
        if bucket_name in bucket_names:
            print(f"✅ S3 bucket '{bucket_name}' verified")
        else:
            print(f"❌ S3 bucket '{bucket_name}' not found")
            return False
    except Exception as e:
        print(f"❌ Failed to verify S3 bucket: {e}")
        return False

    # Verify DynamoDB table
    try:
        response = dynamodb_client.describe_table(TableName=table_name)
        if response['Table']['TableStatus'] == 'ACTIVE':
            print(f"✅ DynamoDB table '{table_name}' verified (status: ACTIVE)")

            # Check GSIs
            gsis = response['Table'].get('GlobalSecondaryIndexes', [])
            gsi_names = [gsi['IndexName'] for gsi in gsis]
            expected_gsis = ['UserIndex', 'StatusIndex']

            for gsi_name in expected_gsis:
                if gsi_name in gsi_names:
                    print(f"✅ GSI '{gsi_name}' verified")
                else:
                    print(f"❌ GSI '{gsi_name}' not found")
                    return False
        else:
            print(f"❌ DynamoDB table '{table_name}' not active (status: {response['Table']['TableStatus']})")
            return False
    except Exception as e:
        print(f"❌ Failed to verify DynamoDB table: {e}")
        return False

    return True


def main():
    """Main function to create LocalStack resources"""
    print("🚀 Setting up LocalStack resources...")

    # Configuration
    bucket_name = 'image-storage-bucket'
    table_name = 'images'

    # LocalStack endpoints
    localstack_endpoint = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
    aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

    print(f"📍 LocalStack endpoint: {localstack_endpoint}")
    print(f"🌍 AWS region: {aws_region}")

    try:
        # Create clients
        s3_client = boto3.client(
            's3',
            endpoint_url=f"{localstack_endpoint}",
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name=aws_region
        )

        dynamodb_client = boto3.client(
            'dynamodb',
            endpoint_url=f"{localstack_endpoint}",
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name=aws_region
        )

        # Create resources
        print("\n📦 Creating S3 bucket...")
        s3_success = create_s3_bucket(s3_client, bucket_name)

        print("\n🗄️  Creating DynamoDB table...")
        dynamodb_success = create_dynamodb_table(dynamodb_client, table_name)

        if s3_success and dynamodb_success:
            # Wait a moment for resources to be ready
            import time
            time.sleep(2)

            # Verify resources
            if verify_resources(s3_client, dynamodb_client, bucket_name, table_name):
                print("\n🎉 All resources created and verified successfully!")
                print(f"   S3 Bucket: {bucket_name}")
                print(f"   DynamoDB Table: {table_name}")
                print("   GSIs: UserIndex, StatusIndex")
                return 0
            else:
                print("\n❌ Resource verification failed!")
                return 1
        else:
            print("\n❌ Failed to create one or more resources!")
            return 1

    except Exception as e:
        print(f"\n💥 Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())