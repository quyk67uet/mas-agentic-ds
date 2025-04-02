from typing import Dict, Any, Callable, List
import time
import logging

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ToolProxy:
    """
    Proxy Pattern implementation for tool interactions
    This proxy adds validation, error handling, and rate limiting to tool calls
    """
    
    def __init__(self, tool_func: Callable, 
                 max_retries: int = 3, 
                 retry_delay: float = 1.0,
                 rate_limit: float = 0.5):
        """
        Initialize the ToolProxy
        
        Args:
            tool_func: The actual tool function to call
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            rate_limit: Minimum time between tool calls in seconds
        """
        self.tool_func = tool_func
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit = rate_limit
        self.last_call_time = 0
        
    def validate_input(self, args: List[Any], kwargs: Dict[str, Any]) -> bool:
        """
        Validate the input parameters for the tool
        Override this in subclasses for specific validation
        
        Returns:
            True if validation passes, False otherwise
        """
        return True
    
    def __call__(self, *args, **kwargs):
        """
        Call the tool function with validation, rate limiting, and error handling
        """
        # Apply rate limiting
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last_call
            logger.info(f"Rate limiting applied. Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        # Validate input
        if not self.validate_input(args, kwargs):
            logger.error(f"Input validation failed for tool call: {self.tool_func.__name__}")
            return {"error": "Input validation failed"}
        
        # Call the tool with retry logic
        for attempt in range(self.max_retries):
            try:
                result = self.tool_func(*args, **kwargs)
                self.last_call_time = time.time()
                return result
            except Exception as e:
                logger.warning(f"Tool call failed (attempt {attempt+1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"Tool call failed after {self.max_retries} attempts: {str(e)}")
                    return {"error": str(e)}

class DatabaseToolProxy(ToolProxy):
    """
    Specific proxy for database tool interactions
    """
    def validate_input(self, args: List[Any], kwargs: Dict[str, Any]) -> bool:
        """
        Validate database tool input
        """
        # Example validation: Check if student_id is present and valid
        if 'student_id' in kwargs:
            student_id = kwargs['student_id']
            if not isinstance(student_id, (int, str)) or not str(student_id).strip():
                logger.error(f"Invalid student_id: {student_id}")
                return False
        return True 