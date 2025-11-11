"""
Configuration module for Project Firefly
"""

import os

class Config:
    """Base configuration"""

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'firefly-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

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
