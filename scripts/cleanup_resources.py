#!/usr/bin/env python3
"""
LocalStack Resource Cleanup Script

This script deletes all AWS resources from LocalStack:
- Empties and deletes S3 bucket
- Deletes DynamoDB table

Usage:
    python cleanup_resources.py
"""

import boto3
import os
import sys


def cleanup_s3_bucket(s3_client, bucket_name):
    """Delete all objects and then delete the bucket"""
    try:
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except:
            print(f"ℹ️  S3 bucket '{bucket_name}' does not exist")
            return True
        
        # Delete all objects in the bucket
        print(f"🗑️  Emptying S3 bucket '{bucket_name}'...")
        try:
            # List and delete all objects
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name)
            
            deleted_count = 0
            for page in pages:
                if 'Contents' in page:
                    objects = [{'Key': obj['Key']} for obj in page['Contents']]
                    s3_client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects}
                    )
                    deleted_count += len(objects)
            
            if deleted_count > 0:
                print(f"   Deleted {deleted_count} object(s)")
        except Exception as e:
            print(f"   Warning: {e}")
        
        # Delete the bucket
        print(f"🗑️  Deleting S3 bucket '{bucket_name}'...")
        s3_client.delete_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket '{bucket_name}' deleted")
        return True
        
    except Exception as e:
        print(f"❌ Failed to delete S3 bucket: {e}")
        return False


def cleanup_dynamodb_table(dynamodb_client, table_name):
    """Delete DynamoDB table"""
    try:
        # Check if table exists
        try:
            dynamodb_client.describe_table(TableName=table_name)
        except dynamodb_client.exceptions.ResourceNotFoundException:
            print(f"ℹ️  DynamoDB table '{table_name}' does not exist")
            return True
        
        # Delete the table
        print(f"🗑️  Deleting DynamoDB table '{table_name}'...")
        dynamodb_client.delete_table(TableName=table_name)
        print(f"✅ DynamoDB table '{table_name}' deleted")
        return True
        
    except Exception as e:
        print(f"❌ Failed to delete DynamoDB table: {e}")
        return False


def main():
    """Main function to cleanup LocalStack resources"""
    print("🧹 Cleaning up LocalStack resources...")
    print()
    
    # Configuration
    bucket_name = os.getenv('S3_BUCKET_NAME', 'image-storage-bucket')
    table_name = os.getenv('DYNAMODB_TABLE_NAME', 'images')
    localstack_endpoint = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
    aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    print(f"📍 LocalStack endpoint: {localstack_endpoint}")
    print(f"🌍 AWS region: {aws_region}")
    print()
    
    # Confirm deletion
    response = input(f"⚠️  Delete all resources? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cleanup cancelled")
        return 0
    
    print()
    
    try:
        # Create clients
        s3_client = boto3.client(
            's3',
            endpoint_url=localstack_endpoint,
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name=aws_region
        )
        
        dynamodb_client = boto3.client(
            'dynamodb',
            endpoint_url=localstack_endpoint,
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name=aws_region
        )
        
        # Cleanup resources
        s3_ok = cleanup_s3_bucket(s3_client, bucket_name)
        print()
        dynamodb_ok = cleanup_dynamodb_table(dynamodb_client, table_name)
        
        # Final result
        print()
        print("="*50)
        if s3_ok and dynamodb_ok:
            print("✅ ALL RESOURCES CLEANED UP SUCCESSFULLY!")
            print("="*50)
            return 0
        else:
            print("⚠️  CLEANUP COMPLETED WITH WARNINGS")
            print("="*50)
            return 1
            
    except Exception as e:
        print(f"\n💥 Error: {e}")
        print("\nMake sure LocalStack is running:")
        print("  docker run -d --name localstack -p 4566:4566 localstack/localstack")
        return 1


if __name__ == '__main__':
    sys.exit(main())