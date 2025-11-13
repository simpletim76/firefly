"""
Database module for Project Firefly
Handles SQLite operations for whitelist, logs, and configuration
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Optional

DB_PATH = os.getenv('DB_PATH', '/app/data/firefly.db')


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize database schema"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Whitelist table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS whitelist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                description TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                added_by TEXT DEFAULT 'admin',
                enabled BOOLEAN DEFAULT 1,
                UNIQUE(domain)
            )
        ''')

        # DNS query logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dns_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                client_ip TEXT NOT NULL,
                domain TEXT NOT NULL,
                query_type TEXT DEFAULT 'A',
                allowed BOOLEAN NOT NULL,
                response_ip TEXT
            )
        ''')

        # Create index for faster log queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_dns_logs_timestamp
            ON dns_logs(timestamp DESC)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_dns_logs_domain
            ON dns_logs(domain)
        ''')

        # Configuration table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Users table for authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')

        # Profiles table - for different family members
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                color TEXT DEFAULT '#3B82F6',
                is_default BOOLEAN DEFAULT 0,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Profile-specific whitelists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profile_whitelists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                domain TEXT NOT NULL,
                description TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                added_by TEXT DEFAULT 'admin',
                enabled BOOLEAN DEFAULT 1,
                FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
                UNIQUE(profile_id, domain)
            )
        ''')

        # Create index for profile whitelist lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_profile_whitelists_lookup
            ON profile_whitelists(profile_id, domain, enabled)
        ''')

        # Devices table - map IP addresses to profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ip_address TEXT UNIQUE NOT NULL,
                profile_id INTEGER,
                last_seen TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE SET NULL
            )
        ''')

        # Create index for device lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_devices_ip
            ON devices(ip_address)
        ''')

        # Add profile_id and device_id to dns_logs if columns don't exist
        try:
            cursor.execute('ALTER TABLE dns_logs ADD COLUMN profile_id INTEGER')
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute('ALTER TABLE dns_logs ADD COLUMN device_id INTEGER')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Insert default admin user (password: admin123 - CHANGE THIS!)
        # Password hash for 'admin123' generated with werkzeug
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash)
            VALUES ('admin', 'scrypt:32768:8:1$qaCAJ7VlgOOYlND7$1518d9e1eb8722a89161e2c097574af6174c40b5a5e8c0f3618e64cc267a1eb80f165da418d9ba94ca983c10c769bbb02a8c9f08f23d0ecc3fddf4aafa9b1722')
        ''')

        # Insert default configuration
        default_configs = [
            ('dns_port', '53'),
            ('web_port', '8080'),
            ('log_retention_days', '30'),
            ('upstream_dns', '8.8.8.8'),
            ('block_response', '0.0.0.0'),
        ]

        for key, value in default_configs:
            cursor.execute('''
                INSERT OR IGNORE INTO config (key, value)
                VALUES (?, ?)
            ''', (key, value))

        conn.commit()
        print("✓ Database initialized successfully")


# Whitelist operations
def add_to_whitelist(domain: str, description: str = '', added_by: str = 'admin') -> bool:
    """Add a domain to the whitelist"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO whitelist (domain, description, added_by)
                VALUES (?, ?, ?)
            ''', (domain.lower().strip(), description, added_by))
            return True
    except sqlite3.IntegrityError:
        return False


def remove_from_whitelist(domain: str) -> bool:
    """Remove a domain from the whitelist"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM whitelist WHERE domain = ?', (domain.lower().strip(),))
        return cursor.rowcount > 0


def get_whitelist(enabled_only: bool = True) -> List[Dict]:
    """Get all whitelisted domains"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = 'SELECT * FROM whitelist'
        if enabled_only:
            query += ' WHERE enabled = 1'
        query += ' ORDER BY domain ASC'

        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]


def is_domain_whitelisted(domain: str) -> bool:
    """Check if a domain is whitelisted"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 1 FROM whitelist
            WHERE domain = ? AND enabled = 1
        ''', (domain.lower().strip(),))
        return cursor.fetchone() is not None


def toggle_whitelist_entry(domain: str) -> bool:
    """Enable/disable a whitelist entry"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE whitelist
            SET enabled = NOT enabled
            WHERE domain = ?
        ''', (domain.lower().strip(),))
        return cursor.rowcount > 0


# DNS log operations
def log_dns_query(client_ip: str, domain: str, query_type: str, allowed: bool, response_ip: str = None,
                 profile_id: int = None, device_id: int = None):
    """Log a DNS query"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO dns_logs (client_ip, domain, query_type, allowed, response_ip, profile_id, device_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (client_ip, domain.lower(), query_type, allowed, response_ip, profile_id, device_id))


def get_recent_logs(limit: int = 100, offset: int = 0) -> List[Dict]:
    """Get recent DNS query logs"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM dns_logs
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        return [dict(row) for row in cursor.fetchall()]


def get_logs_by_domain(domain: str, limit: int = 100) -> List[Dict]:
    """Get logs for a specific domain"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM dns_logs
            WHERE domain LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (f'%{domain.lower()}%', limit))
        return [dict(row) for row in cursor.fetchall()]


def get_stats() -> Dict:
    """Get DNS query statistics"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Total queries
        cursor.execute('SELECT COUNT(*) as total FROM dns_logs')
        total = cursor.fetchone()['total']

        # Allowed queries
        cursor.execute('SELECT COUNT(*) as allowed FROM dns_logs WHERE allowed = 1')
        allowed = cursor.fetchone()['allowed']

        # Blocked queries
        cursor.execute('SELECT COUNT(*) as blocked FROM dns_logs WHERE allowed = 0')
        blocked = cursor.fetchone()['blocked']

        # Whitelisted domains count
        cursor.execute('SELECT COUNT(*) as count FROM whitelist WHERE enabled = 1')
        whitelist_count = cursor.fetchone()['count']

        # Top blocked domains
        cursor.execute('''
            SELECT domain, COUNT(*) as count
            FROM dns_logs
            WHERE allowed = 0
            GROUP BY domain
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_blocked = [dict(row) for row in cursor.fetchall()]

        return {
            'total_queries': total,
            'allowed_queries': allowed,
            'blocked_queries': blocked,
            'whitelist_count': whitelist_count,
            'top_blocked': top_blocked
        }


def cleanup_old_logs(days: int = 30):
    """Remove logs older than specified days"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM dns_logs
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days,))
        deleted = cursor.rowcount
        print(f"✓ Cleaned up {deleted} old log entries")
        return deleted


# Configuration operations
def get_config(key: str) -> Optional[str]:
    """Get a configuration value"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row['value'] if row else None


def set_config(key: str, value: str):
    """Set a configuration value"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO config (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))


def get_all_config() -> Dict[str, str]:
    """Get all configuration values"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM config')
        return {row['key']: row['value'] for row in cursor.fetchall()}


# User operations
def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_last_login(username: str):
    """Update user's last login timestamp"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET last_login = CURRENT_TIMESTAMP
            WHERE username = ?
        ''', (username,))


# Profile operations
def create_profile(name: str, age: int = None, color: str = '#3B82F6',
                   is_default: bool = False, enabled: bool = True) -> int:
    """Create a new profile"""
    with get_db() as conn:
        cursor = conn.cursor()

        # If setting as default, unset other defaults first
        if is_default:
            cursor.execute('UPDATE profiles SET is_default = 0')

        cursor.execute('''
            INSERT INTO profiles (name, age, color, is_default, enabled)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, age, color, is_default, enabled))
        return cursor.lastrowid


def get_profile(profile_id: int) -> Optional[Dict]:
    """Get a profile by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM profiles WHERE id = ?', (profile_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_profiles(enabled_only: bool = True) -> List[Dict]:
    """Get all profiles"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = 'SELECT * FROM profiles'
        if enabled_only:
            query += ' WHERE enabled = 1'
        query += ' ORDER BY name ASC'
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]


def update_profile(profile_id: int, name: str = None, age: int = None, color: str = None,
                   enabled: bool = None, is_default: bool = None) -> bool:
    """Update a profile"""
    with get_db() as conn:
        cursor = conn.cursor()

        # If setting as default, unset other defaults first
        if is_default:
            cursor.execute('UPDATE profiles SET is_default = 0')

        updates = []
        params = []

        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if age is not None:
            updates.append('age = ?')
            params.append(age)
        if color is not None:
            updates.append('color = ?')
            params.append(color)
        if enabled is not None:
            updates.append('enabled = ?')
            params.append(enabled)
        if is_default is not None:
            updates.append('is_default = ?')
            params.append(is_default)

        if not updates:
            return False

        params.append(profile_id)
        query = f"UPDATE profiles SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        return cursor.rowcount > 0


def delete_profile(profile_id: int) -> bool:
    """Delete a profile"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM profiles WHERE id = ?', (profile_id,))
        return cursor.rowcount > 0


def get_default_profile() -> Optional[Dict]:
    """Get the default profile"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM profiles WHERE is_default = 1 LIMIT 1')
        row = cursor.fetchone()
        return dict(row) if row else None


def set_default_profile(profile_id: int) -> bool:
    """Set a profile as default"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Unset all defaults first
        cursor.execute('UPDATE profiles SET is_default = 0')
        # Set the new default
        cursor.execute('UPDATE profiles SET is_default = 1 WHERE id = ?', (profile_id,))
        return cursor.rowcount > 0


# Device operations
def register_device(name: str, ip_address: str, profile_id: int = None) -> int:
    """Register a new device"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO devices (name, ip_address, profile_id, last_seen)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (name, ip_address, profile_id))
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Device already exists, update it
            cursor.execute('''
                UPDATE devices SET name = ?, profile_id = ?, last_seen = CURRENT_TIMESTAMP
                WHERE ip_address = ?
            ''', (name, profile_id, ip_address))
            cursor.execute('SELECT id FROM devices WHERE ip_address = ?', (ip_address,))
            row = cursor.fetchone()
            return row['id'] if row else None


def get_device_by_ip(ip_address: str) -> Optional[Dict]:
    """Get a device by IP address"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM devices WHERE ip_address = ?', (ip_address,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_devices() -> List[Dict]:
    """Get all devices"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, p.name as profile_name, p.color as profile_color
            FROM devices d
            LEFT JOIN profiles p ON d.profile_id = p.id
            ORDER BY d.last_seen DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]


def update_device_profile(device_id: int, profile_id: int) -> bool:
    """Assign a device to a profile"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE devices SET profile_id = ? WHERE id = ?
        ''', (profile_id, device_id))
        return cursor.rowcount > 0


def update_device_last_seen(ip_address: str) -> bool:
    """Update device last seen timestamp"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE devices SET last_seen = CURRENT_TIMESTAMP WHERE ip_address = ?
        ''', (ip_address,))
        return cursor.rowcount > 0


def delete_device(device_id: int) -> bool:
    """Delete a device"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM devices WHERE id = ?', (device_id,))
        return cursor.rowcount > 0


# Profile whitelist operations
def add_to_profile_whitelist(profile_id: int, domain: str, description: str = '', added_by: str = 'admin') -> bool:
    """Add a domain to a profile's whitelist"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO profile_whitelists (profile_id, domain, description, added_by)
                VALUES (?, ?, ?, ?)
            ''', (profile_id, domain.lower().strip(), description, added_by))
            return True
    except sqlite3.IntegrityError:
        return False


def remove_from_profile_whitelist(profile_id: int, domain: str) -> bool:
    """Remove a domain from a profile's whitelist"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM profile_whitelists WHERE profile_id = ? AND domain = ?
        ''', (profile_id, domain.lower().strip()))
        return cursor.rowcount > 0


def get_profile_whitelist(profile_id: int, enabled_only: bool = True) -> List[Dict]:
    """Get all whitelisted domains for a profile"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = 'SELECT * FROM profile_whitelists WHERE profile_id = ?'
        if enabled_only:
            query += ' AND enabled = 1'
        query += ' ORDER BY domain ASC'
        cursor.execute(query, (profile_id,))
        return [dict(row) for row in cursor.fetchall()]


def is_domain_whitelisted_for_profile(domain: str, profile_id: int) -> bool:
    """Check if a domain is whitelisted for a specific profile"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 1 FROM profile_whitelists
            WHERE profile_id = ? AND domain = ? AND enabled = 1
        ''', (profile_id, domain.lower().strip()))
        return cursor.fetchone() is not None


def toggle_profile_whitelist_entry(profile_id: int, domain: str) -> bool:
    """Enable/disable a whitelist entry for a profile"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE profile_whitelists
            SET enabled = NOT enabled
            WHERE profile_id = ? AND domain = ?
        ''', (profile_id, domain.lower().strip()))
        return cursor.rowcount > 0


def copy_whitelist_to_profile(source_profile_id: int, target_profile_id: int) -> int:
    """Copy all whitelist entries from one profile to another"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO profile_whitelists (profile_id, domain, description, added_by)
            SELECT ?, domain, description, added_by
            FROM profile_whitelists
            WHERE profile_id = ? AND enabled = 1
        ''', (target_profile_id, source_profile_id))
        return cursor.rowcount


# Profile statistics
def get_profile_stats(profile_id: int) -> Dict:
    """Get statistics for a specific profile"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Total queries for this profile
        cursor.execute('SELECT COUNT(*) as total FROM dns_logs WHERE profile_id = ?', (profile_id,))
        total = cursor.fetchone()['total']

        # Allowed queries
        cursor.execute('SELECT COUNT(*) as allowed FROM dns_logs WHERE profile_id = ? AND allowed = 1', (profile_id,))
        allowed = cursor.fetchone()['allowed']

        # Blocked queries
        cursor.execute('SELECT COUNT(*) as blocked FROM dns_logs WHERE profile_id = ? AND allowed = 0', (profile_id,))
        blocked = cursor.fetchone()['blocked']

        # Whitelist count
        cursor.execute('SELECT COUNT(*) as count FROM profile_whitelists WHERE profile_id = ? AND enabled = 1', (profile_id,))
        whitelist_count = cursor.fetchone()['count']

        # Top blocked domains
        cursor.execute('''
            SELECT domain, COUNT(*) as count
            FROM dns_logs
            WHERE profile_id = ? AND allowed = 0
            GROUP BY domain
            ORDER BY count DESC
            LIMIT 10
        ''', (profile_id,))
        top_blocked = [dict(row) for row in cursor.fetchall()]

        return {
            'total_queries': total,
            'allowed_queries': allowed,
            'blocked_queries': blocked,
            'whitelist_count': whitelist_count,
            'top_blocked': top_blocked
        }
