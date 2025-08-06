import os
import logging

class MapsConfiguration:
    """Helper class for maps configuration"""
    
    @staticmethod
    def get_google_maps_api_key(config=None):
        """Get Google Maps API key from various sources"""
        logger = logging.getLogger(__name__)
        
        # Try from config object
        if config:
            if hasattr(config, 'get'):
                key = config.get('google_maps_api_key')
                if key:
                    return key
            elif hasattr(config, 'google_maps_api_key'):
                key = getattr(config, 'google_maps_api_key')
                if key:
                    return key
        
        # Try from environment
        key = os.environ.get('GOOGLE_MAPS_API_KEY')
        if key:
            logger.info("Using Google Maps API key from environment")
            return key
        
        # Try from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            key = os.getenv('GOOGLE_MAPS_API_KEY')
            if key:
                logger.info("Using Google Maps API key from .env file")
                return key
        except ImportError:

            pass
        
        logger.warning("No Google Maps API key found")
        return ''
    
    @staticmethod
    def validate_api_key(api_key):
        """Validate if API key is properly formatted"""
        if not api_key:
            return False
        
        # Basic validation - API keys are typically 39 characters
        if len(api_key) < 30:
            return False
        
        # Should start with AIza
        if not api_key.startswith('AIza'):
            return False
        
        return True