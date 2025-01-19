from pathlib import Path
from pydantic_settings import BaseSettings
import logging
import json
from datetime import datetime
import sys

class Settings(BaseSettings):
    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_SCHEMA: str

    # Application settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"


def setup_logger(script_name: str = None) -> logging.Logger:
    """Set up a JSON Lines logger for the given script."""
    # Automatically detect the calling script's name if not provided
    if script_name is None:
        import inspect
        from pathlib import Path
        
        # Get the calling frame (the script that called setup_logger)
        frame = inspect.stack()[1]
        # Get the full path of the calling script
        calling_script = Path(frame.filename)
        # Get project root (parent of lib directory)
        project_root = Path(__file__).parent.parent
        # Get relative path from project root (e.g. 'scripts/demo.py')
        script_name = str(calling_script.relative_to(project_root))

    logger = logging.getLogger(script_name)  # Use full path for logger name
    
    # If logger already has handlers, return it (prevents duplicate handlers)
    if logger.handlers:
        return logger
    
    # Set level from environment
    settings = Settings()
    logger.setLevel(settings.LOG_LEVEL)
    
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create file handler with timestamp for the run, not per script, using .jsonl extension
    file_handler = logging.FileHandler(
        log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl",
        mode='a'  # Append mode
    )
    
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "script": script_name,
                "level": record.levelname,
                "message": record.getMessage(),
                "line_number": record.lineno,
                "function": record.funcName
            }
            
            # Include extra fields if they exist
            if hasattr(record, 'extra'):
                log_data.update(record.extra)
            
            return json.dumps(log_data)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Set JSON formatter for file handler
    file_handler.setFormatter(JsonFormatter())
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Create global settings instance
settings = Settings()