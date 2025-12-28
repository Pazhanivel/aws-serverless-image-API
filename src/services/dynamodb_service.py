"""
DynamoDBService for managing image metadata storage.
"""

from typing import Optional, List, Dict, Any
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from src.config.settings import Settings
from src.models.image_metadata import ImageMetadata
from src.utils.logger import get_logger


logger = get_logger(__name__)


class DynamoDBService:
    """Service for DynamoDB operations."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize DynamoDB service.
        
        Args:
            settings: Settings instance (creates new one if not provided)
        """
        self.settings = settings or Settings()
        
        # Get DynamoDB config
        dynamodb_config = self.settings.get_dynamodb_config()
        self.table_name = dynamodb_config.pop('table_name', self.settings.DYNAMODB_TABLE_NAME)
        self.user_index = dynamodb_config.pop('user_index', self.settings.DYNAMODB_USER_INDEX)
        self.status_index = dynamodb_config.pop('status_index', self.settings.DYNAMODB_STATUS_INDEX)
        
        # Create DynamoDB resource with remaining config (AWS credentials and endpoint)
        dynamodb = boto3.resource('dynamodb', **dynamodb_config)
        self.table = dynamodb.Table(self.table_name)
        
        logger.info(f"DynamoDBService initialized with table: {self.table_name}")
    
    def save_metadata(self, metadata: ImageMetadata, skip_validation: bool = False) -> tuple[bool, Optional[str]]:
        """
        Save image metadata to DynamoDB.
        
        Args:
            metadata: ImageMetadata instance
            skip_validation: Skip validation (useful for processing status with placeholder data)
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate metadata unless skipped
            if not skip_validation:
                is_valid, error = metadata.validate()
                if not is_valid:
                    return False, f"Invalid metadata: {error}"
            
            # Convert to DynamoDB format
            item = metadata.to_dynamodb()
            
            # Save to DynamoDB
            self.table.put_item(Item=item)
            
            logger.info(f"Successfully saved metadata for image: {metadata.image_id}")
            return True, None
            
        except ClientError as e:
            error_msg = f"Failed to save metadata: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error saving metadata: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_metadata(self, image_id: str) -> tuple[bool, Optional[ImageMetadata], Optional[str]]:
        """
        Get image metadata by ID.
        
        Args:
            image_id: Image ID
        
        Returns:
            Tuple of (success, metadata, error_message)
        """
        try:
            response = self.table.get_item(Key={'image_id': image_id})
            
            if 'Item' not in response:
                return True, None, None
            
            metadata = ImageMetadata.from_dynamodb(response['Item'])
            logger.info(f"Successfully retrieved metadata for image: {image_id}")
            return True, metadata, None
            
        except ClientError as e:
            error_msg = f"Failed to get metadata: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error getting metadata: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def query_by_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 100,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, List[ImageMetadata], Optional[Dict[str, Any]], Optional[str]]:
        """
        Query images by user ID using UserIndex GSI.
        
        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum number of items to return
            last_evaluated_key: Pagination token
        
        Returns:
            Tuple of (success, metadata_list, next_key, error_message)
        """
        try:
            # Build query parameters
            query_params = {
                'IndexName': self.user_index,
                'KeyConditionExpression': Key('user_id').eq(user_id),
                'Limit': limit,
                'ScanIndexForward': False  # Sort by upload_timestamp descending (newest first)
            }
            
            # Add status filter if provided
            if status:
                query_params['FilterExpression'] = Attr('status').eq(status)
            
            # Add pagination token if provided
            if last_evaluated_key:
                query_params['ExclusiveStartKey'] = last_evaluated_key
            
            # Execute query
            response = self.table.query(**query_params)
            
            # Convert items to ImageMetadata
            metadata_list = [
                ImageMetadata.from_dynamodb(item)
                for item in response.get('Items', [])
            ]
            
            next_key = response.get('LastEvaluatedKey')
            
            logger.info(f"Successfully queried {len(metadata_list)} images for user: {user_id}")
            return True, metadata_list, next_key, None
            
        except ClientError as e:
            error_msg = f"Failed to query by user: {str(e)}"
            logger.error(error_msg)
            return False, [], None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error querying by user: {str(e)}"
            logger.error(error_msg)
            return False, [], None, error_msg
    
    def query_with_filters(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, List[ImageMetadata], Optional[Dict[str, Any]], Optional[str]]:
        """
        Query images with advanced filters.
        
        Args:
            user_id: User ID
            filters: Dictionary of filters (e.g., {'status': 'active', 'tags': ['vacation']})
            limit: Maximum number of items to return
            last_evaluated_key: Pagination token
        
        Returns:
            Tuple of (success, metadata_list, next_key, error_message)
        """
        try:
            # Build query parameters
            query_params = {
                'IndexName': self.user_index,
                'KeyConditionExpression': Key('user_id').eq(user_id),
                'Limit': limit,
                'ScanIndexForward': False  # Sort by upload_timestamp descending (newest first)
            }
            
            # Build filter expression
            if filters:
                filter_expressions = []
                
                if 'status' in filters:
                    filter_expressions.append(Attr('status').eq(filters['status']))
                
                if 'tags' in filters and filters['tags']:
                    # Check if any of the provided tags exist in the image tags
                    tag_conditions = [Attr('tags').contains(tag) for tag in filters['tags']]
                    if tag_conditions:
                        # Combine with OR logic
                        combined = tag_conditions[0]
                        for condition in tag_conditions[1:]:
                            combined = combined | condition
                        filter_expressions.append(combined)
                
                if 'content_type' in filters:
                    filter_expressions.append(Attr('content_type').eq(filters['content_type']))
                
                if 'min_size' in filters:
                    filter_expressions.append(Attr('size').gte(filters['min_size']))
                
                if 'max_size' in filters:
                    filter_expressions.append(Attr('size').lte(filters['max_size']))
                
                # Combine all filter expressions with AND logic
                if filter_expressions:
                    combined_filter = filter_expressions[0]
                    for expr in filter_expressions[1:]:
                        combined_filter = combined_filter & expr
                    query_params['FilterExpression'] = combined_filter
            
            # Add pagination token if provided
            if last_evaluated_key:
                query_params['ExclusiveStartKey'] = last_evaluated_key
            
            # Execute query
            response = self.table.query(**query_params)
            
            # Convert items to ImageMetadata
            metadata_list = [
                ImageMetadata.from_dynamodb(item)
                for item in response.get('Items', [])
            ]
            
            next_key = response.get('LastEvaluatedKey')
            
            logger.info(f"Successfully queried {len(metadata_list)} images with filters for user: {user_id}")
            return True, metadata_list, next_key, None
            
        except ClientError as e:
            error_msg = f"Failed to query with filters: {str(e)}"
            logger.error(error_msg)
            return False, [], None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error querying with filters: {str(e)}"
            logger.error(error_msg)
            return False, [], None, error_msg
    
    def update_metadata(
        self,
        image_id: str,
        updates: Dict[str, Any]
    ) -> tuple[bool, Optional[ImageMetadata], Optional[str]]:
        """
        Update image metadata.
        
        Args:
            image_id: Image ID
            updates: Dictionary of fields to update
        
        Returns:
            Tuple of (success, updated_metadata, error_message)
        """
        try:
            # Build update expression
            update_parts = []
            expression_attribute_names = {}
            expression_attribute_values = {}
            
            for key, value in updates.items():
                # Skip primary key
                if key == 'image_id':
                    continue
                
                attr_name = f"#{key}"
                attr_value = f":{key}"
                
                update_parts.append(f"{attr_name} = {attr_value}")
                expression_attribute_names[attr_name] = key
                expression_attribute_values[attr_value] = value
            
            if not update_parts:
                return False, None, "No valid fields to update"
            
            update_expression = "SET " + ", ".join(update_parts)
            
            # Execute update
            response = self.table.update_item(
                Key={'image_id': image_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues='ALL_NEW'
            )
            
            # Convert to ImageMetadata
            updated_metadata = ImageMetadata.from_dynamodb(response['Attributes'])
            
            logger.info(f"Successfully updated metadata for image: {image_id}")
            return True, updated_metadata, None
            
        except ClientError as e:
            error_msg = f"Failed to update metadata: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error updating metadata: {str(e)}"
            logger.error(error_msg)
            return False, [], None, error_msg
    
    def update_metadata(self, image_id: str, updates: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Update image metadata fields.
        
        Args:
            image_id: Image ID
            updates: Dictionary of fields to update
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Build update expression
            update_expr_parts = []
            expr_attr_names = {}
            expr_attr_values = {}
            
            for i, (key, value) in enumerate(updates.items()):
                # Use attribute names to handle reserved keywords
                attr_name = f"#attr{i}"
                attr_value = f":val{i}"
                
                update_expr_parts.append(f"{attr_name} = {attr_value}")
                expr_attr_names[attr_name] = key
                expr_attr_values[attr_value] = value
            
            if not update_expr_parts:
                return True, None  # Nothing to update
            
            update_expression = "SET " + ", ".join(update_expr_parts)
            
            # Perform update
            self.table.update_item(
                Key={'image_id': image_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values
            )
            
            logger.info(f"Successfully updated metadata for image: {image_id}")
            return True, None
            
        except ClientError as e:
            error_msg = f"Failed to update metadata: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error updating metadata: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def delete_metadata(self, image_id: str) -> tuple[bool, Optional[str]]:
        """
        Delete image metadata (hard delete).
        
        Args:
            image_id: Image ID
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.table.delete_item(Key={'image_id': image_id})
            
            logger.info(f"Successfully deleted metadata for image: {image_id}")
            return True, None
            
        except ClientError as e:
            error_msg = f"Failed to delete metadata: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error deleting metadata: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def scan_with_filters(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, List[ImageMetadata], Optional[Dict[str, Any]], Optional[str]]:
        """
        Scan table with filters (use sparingly - prefer queries).
        
        Args:
            filters: Dictionary of filters
            limit: Maximum number of items to return
            last_evaluated_key: Pagination token
        
        Returns:
            Tuple of (success, metadata_list, next_key, error_message)
        """
        try:
            # Build scan parameters
            scan_params = {'Limit': limit}
            
            # Build filter expression
            if filters:
                filter_expressions = []
                
                if 'status' in filters:
                    filter_expressions.append(Attr('status').eq(filters['status']))
                
                if 'user_id' in filters:
                    filter_expressions.append(Attr('user_id').eq(filters['user_id']))
                
                if 'tags' in filters and filters['tags']:
                    tag_conditions = [Attr('tags').contains(tag) for tag in filters['tags']]
                    if tag_conditions:
                        combined = tag_conditions[0]
                        for condition in tag_conditions[1:]:
                            combined = combined | condition
                        filter_expressions.append(combined)
                
                if 'content_type' in filters:
                    filter_expressions.append(Attr('content_type').eq(filters['content_type']))
                
                # Combine filter expressions
                if filter_expressions:
                    combined_filter = filter_expressions[0]
                    for expr in filter_expressions[1:]:
                        combined_filter = combined_filter & expr
                    scan_params['FilterExpression'] = combined_filter
            
            # Add pagination token if provided
            if last_evaluated_key:
                scan_params['ExclusiveStartKey'] = last_evaluated_key
            
            # Execute scan
            response = self.table.scan(**scan_params)
            
            # Convert items to ImageMetadata
            metadata_list = [
                ImageMetadata.from_dynamodb(item)
                for item in response.get('Items', [])
            ]
            
            next_key = response.get('LastEvaluatedKey')
            
            logger.info(f"Successfully scanned {len(metadata_list)} images")
            return True, metadata_list, next_key, None
            
        except ClientError as e:
            error_msg = f"Failed to scan with filters: {str(e)}"
            logger.error(error_msg)
            return False, [], None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error scanning with filters: {str(e)}"
            logger.error(error_msg)
            return False, [], None, error_msg
    
    def batch_get_metadata(
        self,
        image_ids: List[str]
    ) -> tuple[bool, List[ImageMetadata], Optional[str]]:
        """
        Get multiple image metadata items in a single request.
        
        Args:
            image_ids: List of image IDs
        
        Returns:
            Tuple of (success, metadata_list, error_message)
        """
        try:
            if not image_ids:
                return True, [], None
            
            # DynamoDB batch_get_item has a limit of 100 items
            if len(image_ids) > 100:
                return False, [], "Cannot fetch more than 100 items at once"
            
            # Build keys
            keys = [{'image_id': image_id} for image_id in image_ids]
            
            # Execute batch get using DynamoDB client (resource doesn't expose batch_get_item)
            aws_config = self.settings.get_aws_config()
            dynamo_client = boto3.client('dynamodb', **aws_config)
            response = dynamo_client.batch_get_item(
                RequestItems={
                    self.table_name: {
                        'Keys': keys
                    }
                }
            )
            
            # Convert items to ImageMetadata
            items = response.get('Responses', {}).get(self.table_name, [])
            metadata_list = [
                ImageMetadata.from_dynamodb(item)
                for item in items
            ]
            
            logger.info(f"Successfully batch retrieved {len(metadata_list)} metadata items")
            return True, metadata_list, None
            
        except ClientError as e:
            error_msg = f"Failed to batch get metadata: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg
        except Exception as e:
            error_msg = f"Unexpected error batch getting metadata: {str(e)}"
            logger.error(error_msg)
            return False, [], error_msg
