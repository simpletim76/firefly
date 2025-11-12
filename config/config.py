"""
Configuration module for Project Firefly
"""

import os
import secrets
import sys

class Config:
    """Base configuration"""

    # Flask settings - SECURITY: Validate SECRET_KEY
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # Validate SECRET_KEY
    if not SECRET_KEY:
        env = os.getenv('FLASK_ENV', 'production')
        if env == 'production':
            print("=" * 70)
            print("ERROR: SECRET_KEY environment variable must be set in production!")
            print("Generate a secure key with: openssl rand -hex 32")
            print("=" * 70)
            sys.exit(1)
        else:
            # Generate random key for development only
            SECRET_KEY = secrets.token_hex(32)
            print("=" * 70)
            print("WARNING: Using auto-generated SECRET_KEY for development")
            print(f"SECRET_KEY={SECRET_KEY}")
            print("Set SECRET_KEY environment variable for production!")
            print("=" * 70)

    # Validate SECRET_KEY strength
    if len(SECRET_KEY) < 32:
        print("WARNING: SECRET_KEY should be at least 32 characters")

    # DNS settings
    DNS_HOST = os.getenv('DNS_HOST', '0.0.0.0')
    DNS_PORT = int(os.getenv('DNS_PORT', '53'))

    # Web settings
    WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT = int(os.getenv('WEB_PORT', '8080'))

    # Database settings
    DB_PATH = os.getenv('DB_PATH', '/app/data/firefly.db')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
