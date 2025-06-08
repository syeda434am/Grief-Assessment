from typing import Any, Dict, Optional, Type, TypeVar
import json
import logging
import re
from pydantic import BaseModel, ValidationError
from com.mhire.app.common.exceptions_utility import rethrow_as_http_exception

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class LLMJsonHandler:
    """Handles parsing and validation of JSON responses from LLMs."""
    
    def clean_json_string(self, json_str: str) -> str:
        """Clean a JSON string by properly escaping quotes and handling newlines."""
        try:
            # Remove any markdown code block markers
            json_str = re.sub(r'```(?:json)?\s*|\s*```', '', json_str)
            
            # Remove any text before the first { and after the last }
            json_str = re.sub(r'^[^{]*', '', json_str)
            json_str = re.sub(r'[^}]*$', '', json_str)
            
            # Handle mixed quote types
            json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)
            
            # Remove newlines within string values
            json_str = re.sub(r'(?<=": ")[^"]*(?=")', lambda m: m.group().replace('\\n', ' ').replace('\n', ' '), json_str)
            
            # Trim whitespace
            return json_str.strip()
            
        except Exception as e:
            logger.error(f"Error cleaning JSON string: {str(e)}")
            rethrow_as_http_exception(e)

    def parse_json(self, json_str: str, max_retries: int = 3, retry_count: int = 0) -> Dict[str, Any]:
        """Parse a potentially malformed JSON string into a Python dict with retry logic."""
        try:
            # First try direct parsing
            return json.loads(json_str)
        except json.JSONDecodeError:
            if retry_count >= max_retries:
                logger.error("Failed to parse JSON after all retries")
                rethrow_as_http_exception(Exception("Invalid JSON response from LLM"))
            
            try:
                cleaned_json = self.clean_json_string(json_str)
                return json.loads(cleaned_json)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON (attempt {retry_count + 1})")
                return self.parse_json(json_str, max_retries, retry_count + 1)

    def validate_model(self, data: Dict[str, Any], model_class: Type[T]) -> T:
        """Validate parsed JSON data against a Pydantic model."""
        try:
            return model_class(**data)
        except ValidationError as e:
            logger.error(f"Data validation failed: {str(e)}")
            rethrow_as_http_exception(e)

    def process_llm_response(self, response_content: str, model_class: Type[T], max_retries: int = 3) -> T:
        """Process an LLM response string into a validated model instance.
        
        Args:
            response_content: The raw response content from the LLM
            model_class: The Pydantic model class to validate against
            max_retries: Maximum number of retry attempts for JSON parsing
            
        Returns:
            An instance of the specified model class
        """
        try:
            # Parse JSON with retries
            json_data = self.parse_json(response_content, max_retries)
            
            # Validate against model
            return self.validate_model(json_data, model_class)
            
        except Exception as e:
            logger.error(f"Failed to process LLM response: {str(e)}")
            rethrow_as_http_exception(e)
