#!/usr/bin/env python3
"""
Project Firefly - Main Entry Point
Starts DNS server and web application
"""

import os
import sys
import logging
import time
from pathlib import Path

# Configure logging
log_handlers = [logging.StreamHandler(sys.stdout)]

# Try to add file handler if possible (may fail due to volume mount permissions)
try:
    log_file = Path('/app/logs/firefly.log')
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_handlers.append(logging.FileHandler(str(log_file)))
except (OSError, PermissionError) as e:
    # If we can't write to log file, just use stdout (common in Docker)
    print(f"Warning: Cannot write to log file: {e}. Logging to stdout only.")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)

logger = logging.getLogger(__name__)

# Ensure data directory exists (may fail with volume mount permission issues)
try:
    data_dir = Path('/app/data')
    data_dir.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError) as e:
    logger.warning(f"Cannot create data directory: {e}")

try:
    logs_dir = Path('/app/logs')
    logs_dir.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError) as e:
    logger.warning(f"Cannot create logs directory: {e}")

# Import application modules
from app.database import init_database
from app.dns_server import start_dns_server
from app.web_app import create_app


def main():
    """Main application entry point"""

    logger.info("=" * 60)
    logger.info("🔥 Project Firefly - DNS Filtering Application")
    logger.info("=" * 60)

    # Initialize database
    logger.info("Initializing database...")
    try:
        init_database()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

    # Get configuration from environment
    dns_host = os.getenv('DNS_HOST', '0.0.0.0')
    dns_port = int(os.getenv('DNS_PORT', '53'))
    web_host = os.getenv('WEB_HOST', '0.0.0.0')
    web_port = int(os.getenv('WEB_PORT', '8080'))

    # Start DNS server
    logger.info(f"Starting DNS server on {dns_host}:{dns_port}...")
    try:
        start_dns_server(host=dns_host, port=dns_port)
        logger.info("✓ DNS server started successfully")
    except Exception as e:
        logger.error(f"Failed to start DNS server: {e}")
        logger.error("Make sure to run with appropriate permissions for port 53")
        sys.exit(1)

    # Give DNS server a moment to start
    time.sleep(1)

    # Start web application
    logger.info(f"Starting web interface on {web_host}:{web_port}...")
    try:
        app = create_app()

        logger.info("=" * 60)
        logger.info("✓ Project Firefly is running!")
        logger.info(f"  DNS Server:    {dns_host}:{dns_port}")
        logger.info(f"  Web Interface: http://{web_host}:{web_port}")
        logger.info("  Default login: admin / admin123")
        logger.info("=" * 60)

        # Run Flask application
        # In production, this would be run with gunicorn
        if os.getenv('FLASK_ENV') == 'development':
            app.run(host=web_host, port=web_port, debug=True)
        else:
            # Use gunicorn in production
            from gunicorn.app.base import BaseApplication

            class StandaloneApplication(BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()

                def load_config(self):
                    for key, value in self.options.items():
                        self.cfg.set(key.lower(), value)

                def load(self):
                    return self.application

            options = {
                'bind': f'{web_host}:{web_port}',
                'workers': 2,
                'worker_class': 'sync',
                'accesslog': '/app/logs/access.log',
                'errorlog': '/app/logs/error.log',
                'loglevel': 'info',
            }

            StandaloneApplication(app, options).run()

    except Exception as e:
        logger.error(f"Failed to start web application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nShutting down Project Firefly...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
