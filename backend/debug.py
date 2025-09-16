import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Configure logging with new log_config, but set to DEBUG for debug mode
from log_config import configure_logging
logger = configure_logging(logging.DEBUG)

# Import centralized database initialization and startup loader
from database import get_db
from services.startup_loader import StartupLoader

def initialize_for_debugging():
    """Initialize the backend for debugging"""
    logger.info("Initializing backend for debugging...")
    
    # Initialize database, perform migrations, and load data using StartupLoader
    StartupLoader.initialize_backend()

def main():
    """Run the Flask app in debug mode with VS Code integration"""
    try:
        logger.info("Starting the Flask application in debug mode")
        
        # Initialize backend with all required steps
        initialize_for_debugging()
        
        # Disable Flask's reloader for VS Code compatibility
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = 'true'
        os.environ['WERKZEUG_RUN_MAIN'] = 'true'  # Important for VS Code debugging
        
        # Set port
        port = int(os.environ.get('PORT', '5050'))
        os.environ['PORT'] = str(port)
        
        # Import app
        import app
        
        # Run the Flask app with settings for VS Code debugging
        logger.info(f"Running Flask app on port {port} for debugging")
        app.app.run(
            host='0.0.0.0', 
            port=port, 
            debug=True, 
            use_reloader=False,  # Must be False for VS Code debugging
            use_debugger=False   # Let VS Code handle debugging
        )
        
    except Exception as e:
        logger.exception(f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
