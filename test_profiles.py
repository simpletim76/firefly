#!/usr/bin/env python3
"""
Test script for multi-profile functionality
Tests database operations and profile-based filtering
"""

import os
import sys
from pathlib import Path

# Set up path
sys.path.insert(0, str(Path(__file__).parent))
os.environ['DB_PATH'] = './data/firefly.db'

from app.database import (
    init_database,
    # Profile operations
    create_profile, get_all_profiles, get_profile,
    # Device operations
    register_device, get_all_devices, get_device_by_ip, update_device_profile,
    # Profile whitelist operations
    add_to_profile_whitelist, get_profile_whitelist, is_domain_whitelisted_for_profile,
    get_profile_stats
)

def test_multi_profile():
    """Test multi-profile functionality"""

    print("=" * 70)
    print("🔥 Testing Project Firefly Multi-Profile Support")
    print("=" * 70)

    # Initialize database
    print("\n1️⃣  Initializing database...")
    init_database()
    print("   ✓ Database initialized")

    # Create profiles for two kids
    print("\n2️⃣  Creating profiles...")
    emma_id = create_profile(name="Emma", age=6, color="#FF69B4")  # Pink
    jake_id = create_profile(name="Jake", age=9, color="#4169E1")  # Royal Blue
    print(f"   ✓ Created profile: Emma (ID: {emma_id}, Age: 6)")
    print(f"   ✓ Created profile: Jake (ID: {jake_id}, Age: 9)")

    # Add age-appropriate domains to Emma's whitelist (6 years old)
    print("\n3️⃣  Adding domains to Emma's whitelist (age 6)...")
    emma_domains = [
        ('pbskids.org', 'PBS Kids educational games'),
        ('nickjr.com', 'Nick Jr shows'),
        ('youtube.com', 'YouTube Kids content'),
        ('google.com', 'Search engine'),
    ]

    for domain, desc in emma_domains:
        add_to_profile_whitelist(emma_id, domain, desc)
        print(f"   ✓ Added: {domain}")

    # Add age-appropriate domains to Jake's whitelist (9 years old)
    print("\n4️⃣  Adding domains to Jake's whitelist (age 9)...")
    jake_domains = [
        ('scratch.mit.edu', 'Scratch programming'),
        ('khanacademy.org', 'Khan Academy learning'),
        ('minecraft.net', 'Minecraft'),
        ('youtube.com', 'YouTube'),
        ('google.com', 'Search engine'),
        ('wikipedia.org', 'Wikipedia'),
    ]

    for domain, desc in jake_domains:
        add_to_profile_whitelist(jake_id, domain, desc)
        print(f"   ✓ Added: {domain}")

    # Register devices
    print("\n5️⃣  Registering devices...")
    emma_ipad = register_device("Emma's iPad", "192.168.1.10", emma_id)
    jake_tablet = register_device("Jake's Tablet", "192.168.1.11", jake_id)
    print(f"   ✓ Registered: Emma's iPad (192.168.1.10) → Emma's profile")
    print(f"   ✓ Registered: Jake's Tablet (192.168.1.11) → Jake's profile")

    # Test domain filtering
    print("\n6️⃣  Testing profile-based domain filtering...")

    # Test Emma's profile
    print("\n   Emma's Profile (Age 6):")
    test_domains_emma = [
        'pbskids.org',
        'scratch.mit.edu',  # Should be blocked
        'youtube.com',
        'facebook.com',  # Should be blocked
    ]

    for domain in test_domains_emma:
        allowed = is_domain_whitelisted_for_profile(domain, emma_id)
        status = "✓ ALLOWED" if allowed else "✗ BLOCKED"
        print(f"      {status}: {domain}")

    # Test Jake's profile
    print("\n   Jake's Profile (Age 9):")
    test_domains_jake = [
        'pbskids.org',  # Should be blocked (not in his list)
        'scratch.mit.edu',
        'minecraft.net',
        'facebook.com',  # Should be blocked
    ]

    for domain in test_domains_jake:
        allowed = is_domain_whitelisted_for_profile(domain, jake_id)
        status = "✓ ALLOWED" if allowed else "✗ BLOCKED"
        print(f"      {status}: {domain}")

    # Test subdomain support
    print("\n7️⃣  Testing subdomain support...")
    print("   Emma's profile - testing subdomains of youtube.com:")
    subdomains = ['www.youtube.com', 'm.youtube.com', 'kids.youtube.com']
    for subdomain in subdomains:
        allowed = is_domain_whitelisted_for_profile(subdomain, emma_id)
        status = "✓ ALLOWED" if allowed else "✗ BLOCKED"
        print(f"      {status}: {subdomain}")

    # Display profile summaries
    print("\n8️⃣  Profile Summaries:")
    for profile_id, profile_name in [(emma_id, "Emma"), (jake_id, "Jake")]:
        profile = get_profile(profile_id)
        whitelist = get_profile_whitelist(profile_id)
        print(f"\n   📋 {profile_name}'s Profile:")
        print(f"      Age: {profile['age']}")
        print(f"      Color: {profile['color']}")
        print(f"      Whitelisted domains: {len(whitelist)}")
        print(f"      Domains: {', '.join([d['domain'] for d in whitelist[:5]])}")
        if len(whitelist) > 5:
            print(f"               ...and {len(whitelist) - 5} more")

    # Display devices
    print("\n9️⃣  Registered Devices:")
    devices = get_all_devices()
    for device in devices:
        profile_name = device['profile_name'] or 'Unassigned'
        print(f"   📱 {device['name']} ({device['ip_address']})")
        print(f"      → Assigned to: {profile_name}")

    print("\n" + "=" * 70)
    print("✅ Multi-Profile Support Test Complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Rebuild container: docker compose down && docker compose build")
    print("2. Start container: docker compose up -d")
    print("3. Check logs: docker compose logs -f")
    print("4. The DNS server will now filter based on device IP → profile → whitelist")
    print("\n💡 Tip: Devices making DNS queries will be auto-registered.")
    print("   Use the API or database to assign them to profiles.")
    print("=" * 70)

if __name__ == '__main__':
    try:
        test_multi_profile()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
