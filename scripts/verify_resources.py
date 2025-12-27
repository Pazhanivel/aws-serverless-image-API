#!/usr/bin/env python3
"""
LocalStack Resource Verification Script

This script verifies that all AWS resources are created correctly in LocalStack.

Usage:
    python verify_resources.py
"""

import boto3
import os
import sys


def verify_s3_bucket(s3_client, bucket_name):
    """Verify S3 bucket exists"""
    try:
        buckets = s3_client.list_buckets()
        bucket_names = [b['Name'] for b in buckets['Buckets']]
        
        if bucket_name in bucket_names:
            print(f"✅ S3 bucket '{bucket_name}' exists")
            
            # Check if we can access the bucket
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ S3 bucket '{bucket_name}' is accessible")
            return True
        else:
            print(f"❌ S3 bucket '{bucket_name}' not found")
            return False
    except Exception as e:
        print(f"❌ Error verifying S3 bucket: {e}")
        return False


def verify_dynamodb_table(dynamodb_client, table_name):
    """Verify DynamoDB table exists with correct configuration"""
    try:
        response = dynamodb_client.describe_table(TableName=table_name)
        table = response['Table']
        
        # Check table status
        status = table['TableStatus']
        if status == 'ACTIVE':
            print(f"✅ DynamoDB table '{table_name}' is ACTIVE")
        else:
            print(f"⚠️  DynamoDB table '{table_name}' status: {status}")
            return False
        
        # Check primary key
        key_schema = table['KeySchema']
        primary_key = next((k for k in key_schema if k['KeyType'] == 'HASH'), None)
        if primary_key and primary_key['AttributeName'] == 'image_id':
            print(f"✅ Primary key 'image_id' verified")
        else:
            print(f"❌ Primary key configuration incorrect")
            return False
        
        # Check GSIs
        gsis = table.get('GlobalSecondaryIndexes', [])
        gsi_names = [gsi['IndexName'] for gsi in gsis]
        expected_gsis = ['UserIndex', 'StatusIndex']
        
        all_gsis_found = True
        for gsi_name in expected_gsis:
            if gsi_name in gsi_names:
                gsi = next(g for g in gsis if g['IndexName'] == gsi_name)
                gsi_status = gsi.get('IndexStatus', 'ACTIVE')
                if gsi_status == 'ACTIVE':
                    print(f"✅ GSI '{gsi_name}' is ACTIVE")
                else:
                    print(f"⚠️  GSI '{gsi_name}' status: {gsi_status}")
                    all_gsis_found = False
            else:
                print(f"❌ GSI '{gsi_name}' not found")
                all_gsis_found = False
        
        return all_gsis_found
        
    except dynamodb_client.exceptions.ResourceNotFoundException:
        print(f"❌ DynamoDB table '{table_name}' not found")
        return False
    except Exception as e:
        print(f"❌ Error verifying DynamoDB table: {e}")
        return False


def list_all_resources(s3_client, dynamodb_client):
    """List all S3 buckets and DynamoDB tables"""
    print("\n" + "="*50)
    print("ALL RESOURCES IN LOCALSTACK")
    print("="*50)
    
    # List S3 buckets
    print("\n📦 S3 Buckets:")
    try:
        buckets = s3_client.list_buckets()
        if buckets['Buckets']:
            for bucket in buckets['Buckets']:
                print(f"  - {bucket['Name']}")
        else:
            print("  (none)")
    except Exception as e:
        print(f"  Error: {e}")
    
    # List DynamoDB tables
    print("\n🗄️  DynamoDB Tables:")
    try:
        tables = dynamodb_client.list_tables()
        if tables['TableNames']:
            for table in tables['TableNames']:
                print(f"  - {table}")
        else:
            print("  (none)")
    except Exception as e:
        print(f"  Error: {e}")


def main():
    """Main function to verify LocalStack resources"""
    print("🔍 Verifying LocalStack Resources...")
    print()
    
    # Configuration
    bucket_name = os.getenv('S3_BUCKET_NAME', 'image-storage-bucket')
    table_name = os.getenv('DYNAMODB_TABLE_NAME', 'images')
    localstack_endpoint = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
    aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    print(f"📍 LocalStack endpoint: {localstack_endpoint}")
    print(f"🌍 AWS region: {aws_region}")
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
        
        # Verify resources
        print("="*50)
        print("VERIFYING PROJECT RESOURCES")
        print("="*50)
        print()
        
        s3_ok = verify_s3_bucket(s3_client, bucket_name)
        print()
        dynamodb_ok = verify_dynamodb_table(dynamodb_client, table_name)
        
        # List all resources
        list_all_resources(s3_client, dynamodb_client)
        
        # Final result
        print("\n" + "="*50)
        if s3_ok and dynamodb_ok:
            print("✅ ALL RESOURCES VERIFIED SUCCESSFULLY!")
            print("="*50)
            print()
            print(f"   S3 Bucket: {bucket_name}")
            print(f"   DynamoDB Table: {table_name}")
            print("   GSIs: UserIndex, StatusIndex")
            print()
            return 0
        else:
            print("❌ RESOURCE VERIFICATION FAILED!")
            print("="*50)
            print()
            print("Run 'python create_resources.py' to create missing resources")
            print()
            return 1
            
    except Exception as e:
        print(f"\n💥 Error: {e}")
        print("\nMake sure LocalStack is running:")
        print("  docker run -d --name localstack -p 4566:4566 localstack/localstack")
        return 1


if __name__ == '__main__':
    sys.exit(main())