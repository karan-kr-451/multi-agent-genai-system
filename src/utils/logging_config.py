import logging
import logging.config
import os
import json
from typing import Optional
from datetime import datetime

def setup_logging(log_dir: Optional[str] = None) -> None:
    """
    Set up logging configuration for the application.
    Creates log directory if it doesn't exist.
    
    Args:
        log_dir: Optional directory for log files. Defaults to 'logs' in current directory.
    """
    if not log_dir:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log filenames with timestamps
    timestamp = datetime.now().strftime('%Y%m%d')
    general_log = os.path.join(log_dir, f'app_{timestamp}.log')
    error_log = os.path.join(log_dir, f'error_{timestamp}.log')
    
    # Define logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s'
            },
            'json': {
                'class': 'src.utils.logging_config.JsonFormatter',
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': general_log,
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': error_log,
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            },
            'json_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'json',
                'filename': os.path.join(log_dir, f'json_{timestamp}.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'file', 'error_file', 'json_file']
        },
        'loggers': {
            'mcp_server': {
                'level': 'DEBUG',
                'handlers': ['console', 'file', 'error_file', 'json_file'],
                'propagate': False
            },
            'agents': {
                'level': 'DEBUG',
                'handlers': ['console', 'file', 'error_file', 'json_file'],
                'propagate': False
            },
            'tools': {
                'level': 'DEBUG',
                'handlers': ['console', 'file', 'error_file', 'json_file'],
                'propagate': False
            }
        }
    }
    
    # Apply configuration
    try:
        logging.config.dictConfig(config)
        logging.info("Logging configuration loaded successfully")
    except Exception as e:
        # Fallback to basic configuration if loading fails
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        logging.error(f"Failed to load logging configuration: {str(e)}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    Creates a new logger if one doesn't exist.
    
    Args:
        name: Name of the logger
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as JSON.
        
        Args:
            record: The log record to format
            
        Returns:
            str: JSON formatted log entry
        """
        # Create base log entry
        log_entry = {
            'timestamp': self.formatTime(record),
            'name': record.name,
            'level': record.levelname,
            'message': record.getMessage(),
            'pathname': record.pathname,
            'lineno': record.lineno,
            'function': record.funcName,
            'thread': record.thread,
            'thread_name': record.threadName,
            'process': record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            formatted_exception = self.formatException(record.exc_info)
            log_entry['exception'] = {
                'type': exc_type.__name__ if exc_type else None,
                'message': str(exc_value) if exc_value else None,
                'traceback': formatted_exception
            }
        
        # Add custom fields from the extra parameter
        if hasattr(record, 'job_id'):
            log_entry['job_id'] = record.job_id
        if hasattr(record, 'agent'):
            log_entry['agent'] = record.agent
        if hasattr(record, 'tool'):
            log_entry['tool'] = record.tool
        if hasattr(record, 'state'):
            log_entry['state'] = record.state
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
            
        # Filter out sensitive data
        self._filter_sensitive_data(log_entry)
        
        return json.dumps(log_entry)
    
    def _filter_sensitive_data(self, log_entry: dict) -> None:
        """
        Filter out sensitive data from the log entry.
        Modifies the log_entry dict in place.
        
        Args:
            log_entry: The log entry to filter
        """
        sensitive_keys = {
            'password', 'token', 'api_key', 'secret', 'auth',
            'authorization', 'redis_password'
        }
        
        def redact_value(value):
            if isinstance(value, dict):
                return {k: redact_value(v) if not any(key in k.lower() for key in sensitive_keys) 
                       else '***REDACTED***' for k, v in value.items()}
            elif isinstance(value, str):
                return '***REDACTED***' if any(key in str(value).lower() for key in sensitive_keys) else value
            return value
        
        # Filter message field
        if 'message' in log_entry:
            message = log_entry['message']
            for key in sensitive_keys:
                if key in message.lower():
                    parts = message.split()
                    filtered_parts = [
                        '***REDACTED***' if key in part.lower() else part 
                        for part in parts
                    ]
                    log_entry['message'] = ' '.join(filtered_parts)
        
        # Filter other fields
        for key, value in log_entry.items():
            if isinstance(value, (dict, str)):
                log_entry[key] = redact_value(value)