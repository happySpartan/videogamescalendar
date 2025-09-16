import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    # Application settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_default_secret_key'
    
    # IGDB API credentials
    TWITCH_CLIENT_ID = os.environ.get('TWITCH_CLIENT_ID') or 'your_twitch_client_id'
    TWITCH_CLIENT_SECRET = os.environ.get('TWITCH_CLIENT_SECRET') or 'your_twitch_client_secret'
    
    # API Settings
    API_CACHE_HOURS = int(os.environ.get('API_CACHE_HOURS', 168))  # Changed from 24 to 168 (7 days)
    
    # Cache refresh interval in hours
    CACHE_REFRESH_HOURS = int(os.environ.get('CACHE_REFRESH_HOURS', 168))  # Changed from 24 to 168 (7 days)
    GAMES_REFRESH_HOURS = int(os.environ.get('GAMES_REFRESH_HOURS', 168))  # Changed from 12 to 168 (7 days)
    
    # Additional settings that might be useful
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
    
    # Admin settings
    ADMIN_KEY = os.environ.get('ADMIN_KEY') or 'admin_secret_key'
    
    @classmethod
    def is_configured(cls):
        """Check if essential configuration is present"""
        return bool(cls.TWITCH_CLIENT_ID and cls.TWITCH_CLIENT_SECRET)