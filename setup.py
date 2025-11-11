#!/usr/bin/env python3
"""
Setup and verification script for Project Firefly
"""

import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_database, add_to_whitelist, get_whitelist, get_stats


def main():
    """Run setup and verification"""

    print("=" * 60)
    print("🔥 Project Firefly - Setup & Verification")
    print("=" * 60)

    # Ensure data directory exists
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)

    # Set database path for local testing
    os.environ['DB_PATH'] = str(data_dir / 'firefly.db')

    # Initialize database
    print("\n1. Initializing database...")
    try:
        init_database()
        print("   ✓ Database initialized successfully")
    except Exception as e:
        print(f"   ✗ Database initialization failed: {e}")
        sys.exit(1)

    # Add some example domains to whitelist
    print("\n2. Adding example domains to whitelist...")
    example_domains = [
        ('google.com', 'Google services'),
        ('github.com', 'GitHub'),
        ('pypi.org', 'Python Package Index'),
    ]

    for domain, description in example_domains:
        if add_to_whitelist(domain, description, 'setup'):
            print(f"   ✓ Added: {domain}")
        else:
            print(f"   - Already exists: {domain}")

    # Verify whitelist
    print("\n3. Verifying whitelist...")
    whitelist = get_whitelist()
    print(f"   ✓ Whitelist contains {len(whitelist)} domains")

    # Show stats
    print("\n4. Database statistics...")
    stats = get_stats()
    print(f"   - Total queries: {stats['total_queries']}")
    print(f"   - Allowed: {stats['allowed_queries']}")
    print(f"   - Blocked: {stats['blocked_queries']}")
    print(f"   - Whitelist count: {stats['whitelist_count']}")

    print("\n" + "=" * 60)
    print("✓ Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Build the Docker image: docker-compose build")
    print("2. Start the container: docker-compose up -d")
    print("3. Access web interface: http://localhost:8080")
    print("4. Login with: admin / admin123")
    print("\nIMPORTANT: Change default password after first login!")
    print("=" * 60)


if __name__ == '__main__':
    main()
