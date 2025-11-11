#!/usr/bin/env python3
"""
Script to fix the admin password in existing database
Resets the admin password to 'admin123'
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from werkzeug.security import generate_password_hash

def fix_admin_password():
    """Update admin password in the database"""

    # Database path
    db_path = os.getenv('DB_PATH', './data/firefly.db')

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("The database will be created with the correct password when you start the container.")
        return

    print("🔧 Fixing admin password...")
    print(f"Database: {db_path}")

    # Generate correct password hash
    password_hash = generate_password_hash('admin123')
    print(f"Generated new password hash")

    # Update database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Update the admin password
        cursor.execute('''
            UPDATE users
            SET password_hash = ?
            WHERE username = 'admin'
        ''', (password_hash,))

        conn.commit()

        if cursor.rowcount > 0:
            print("✅ Admin password updated successfully!")
            print("   Username: admin")
            print("   Password: admin123")
            print("\n⚠️  IMPORTANT: Change this password after logging in!")
        else:
            print("⚠️  No admin user found. Creating one...")
            cursor.execute('''
                INSERT INTO users (username, password_hash)
                VALUES ('admin', ?)
            ''', (password_hash,))
            conn.commit()
            print("✅ Admin user created successfully!")

        conn.close()

    except Exception as e:
        print(f"❌ Error updating password: {e}")
        sys.exit(1)

if __name__ == '__main__':
    fix_admin_password()
