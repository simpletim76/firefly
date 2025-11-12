"""
Device Manager module for Project Firefly
Handles device identification and profile mapping with caching
"""

import logging
from typing import Optional, Tuple
from app.database import (
    get_device_by_ip,
    register_device,
    update_device_last_seen,
    get_default_profile
)

logger = logging.getLogger(__name__)


class DeviceManager:
    """
    Manages device identification and profile mapping
    Uses caching for performance
    """

    def __init__(self):
        """Initialize device manager with empty caches"""
        self.device_cache = {}  # ip → (device_id, profile_id)
        self.cache_hits = 0
        self.cache_misses = 0

    def get_profile_for_ip(self, client_ip: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Get profile ID and device ID for an IP address

        Args:
            client_ip: Client IP address

        Returns:
            Tuple of (device_id, profile_id) or (None, None)
        """
        # Check cache first
        if client_ip in self.device_cache:
            self.cache_hits += 1
            return self.device_cache[client_ip]

        self.cache_misses += 1

        # Look up device in database
        device = get_device_by_ip(client_ip)

        if device:
            # Update last seen timestamp
            update_device_last_seen(client_ip)

            # Cache the result
            result = (device['id'], device['profile_id'])
            self.device_cache[client_ip] = result

            logger.debug(f"Device found: {device['name']} (IP: {client_ip}, Profile: {device['profile_id']})")
            return result
        else:
            # Unknown device - auto-register with no profile
            logger.info(f"New device detected: {client_ip}")
            try:
                device_id = register_device(
                    name=f"Device-{client_ip}",
                    ip_address=client_ip,
                    profile_id=None
                )
                result = (device_id, None)
                self.device_cache[client_ip] = result
                return result
            except Exception as e:
                logger.error(f"Failed to register device {client_ip}: {e}")
                return (None, None)

    def clear_cache(self):
        """Clear the device cache (call after profile assignments change)"""
        self.device_cache.clear()
        logger.info("Device cache cleared")

    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0

        return {
            'cache_size': len(self.device_cache),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': f"{hit_rate:.1f}%"
        }


# Global device manager instance
_device_manager = None


def get_device_manager() -> DeviceManager:
    """Get or create the global device manager instance"""
    global _device_manager
    if _device_manager is None:
        _device_manager = DeviceManager()
        logger.info("Device manager initialized")
    return _device_manager


def clear_device_cache():
    """Clear the device cache (helper function)"""
    manager = get_device_manager()
    manager.clear_cache()
