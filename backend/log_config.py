import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Try to import colorlog, but provide a fallback if not available
try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False
    print("Warning: colorlog package not found. Installing with 'pip install colorlog' for colored logs.")

def configure_logging(log_level=logging.INFO):
    """Configure logging for the application with colored output when available"""
    # Clear any existing handlers (important for module reloads)
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    
    # Add console handler with appropriate formatter
    console_handler = logging.StreamHandler(sys.stdout)
    
    if COLORLOG_AVAILABLE:
        # Define color scheme for different log levels
        color_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        )
        console_handler.setFormatter(color_formatter)
    else:
        # Standard formatter without colors - Fixed typo from 'levellevel' to 'levelname'
        standard_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(standard_formatter)
    
    # Configure root logger
    root.setLevel(log_level)
    root.addHandler(console_handler)
    
    # Configure specific loggers
    # Set SQLAlchemy engine to WARNING level to reduce SQL statement logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    # Only show SQLAlchemy pool DEBUG messages when in DEBUG mode
    logging.getLogger('sqlalchemy.pool').setLevel(
        logging.DEBUG if log_level == logging.DEBUG else logging.WARNING
    )
    
    # Set up file logging if desired (no colors in files)
    log_to_file = os.environ.get('LOG_TO_FILE', 'false').lower() in ('true', '1', 't')
    if log_to_file:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Fixed typo from 'levellevel' to 'levelname'
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(file_formatter)
        
        # Add handler to root logger
        root.addHandler(file_handler)
    
    # Return root logger
    return root
