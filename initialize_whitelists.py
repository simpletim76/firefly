#!/usr/bin/env python3
"""
Comprehensive Whitelist Initialization for Project Firefly
Creates Aurora (age 9) and Harriet (age 6) profiles with age-appropriate domains
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from database import (
    init_db, create_profile, add_to_profile_whitelist,
    register_device, get_profile, get_profile_whitelist
)


def initialize_profiles():
    """Initialize profiles with comprehensive whitelists"""

    print("=" * 60)
    print("Project Firefly - Whitelist Initialization")
    print("=" * 60)
    print()

    # Initialize database
    print("📊 Initializing database...")
    init_db()

    # Create profiles
    print("\n👧 Creating profiles...")
    harriet_id = create_profile(
        name="Harriet",
        age=6,
        color="#FF69B4",  # Pink
        is_default=False,
        enabled=True
    )

    aurora_id = create_profile(
        name="Aurora",
        age=9,
        color="#9370DB",  # Purple
        is_default=False,
        enabled=True
    )

    print(f"   ✓ Harriet (age 6) - Profile ID: {harriet_id}")
    print(f"   ✓ Aurora (age 9) - Profile ID: {aurora_id}")

    # Essential domains (both profiles)
    essential_domains = [
        ('google.com', 'Google search'),
        ('googleapis.com', 'Google APIs'),
        ('gstatic.com', 'Google static content'),
        ('googleusercontent.com', 'Google user content'),
        ('youtube.com', 'YouTube'),
        ('ytimg.com', 'YouTube images'),
        ('youtu.be', 'YouTube short links'),
        ('ggpht.com', 'YouTube thumbnails'),
        ('googlevideo.com', 'YouTube videos'),
    ]

    # Streaming services (both profiles)
    streaming_domains = [
        # Disney+
        ('disneyplus.com', 'Disney+ streaming'),
        ('disney.com', 'Disney main site'),
        ('dssott.com', 'Disney+ streaming CDN'),
        ('bamgrid.com', 'Disney+ API'),
        ('disney-plus.net', 'Disney+ CDN'),
        ('disneystreaming.com', 'Disney streaming services'),

        # Netflix
        ('netflix.com', 'Netflix streaming'),
        ('nflxext.com', 'Netflix external'),
        ('nflximg.net', 'Netflix images'),
        ('nflxvideo.net', 'Netflix video CDN'),
        ('nflxso.net', 'Netflix streaming'),
    ]

    # Educational - Young (Harriet age 6)
    harriet_educational = [
        ('pbskids.org', 'PBS Kids educational games'),
        ('nickjr.com', 'Nick Jr shows and games'),
        ('starfall.com', 'Phonics and reading'),
        ('abcya.com', 'Educational games'),
        ('funbrain.com', 'Math and reading games'),
        ('sesameworkshop.org', 'Sesame Street'),
        ('coolmathgames.com', 'Math games'),
        ('nationalgeographic.com', 'National Geographic'),
        ('natgeokids.com', 'National Geographic Kids'),
        ('kids.nationalgeographic.com', 'Nat Geo Kids subdomain'),
    ]

    # Educational - Older (Aurora age 9)
    aurora_educational = [
        ('scratch.mit.edu', 'Scratch programming'),
        ('khanacademy.org', 'Khan Academy learning'),
        ('code.org', 'Coding tutorials'),
        ('coolmath.com', 'Math lessons and games'),
        ('coolmathgames.com', 'Math games'),
        ('funbrain.com', 'Educational games'),
        ('nationalgeographic.com', 'National Geographic'),
        ('natgeokids.com', 'National Geographic Kids'),
        ('kids.nationalgeographic.com', 'Nat Geo Kids subdomain'),
        ('britannica.com', 'Encyclopedia Britannica'),
        ('kids.britannica.com', 'Britannica Kids'),
        ('nasa.gov', 'NASA'),
        ('wikipedia.org', 'Wikipedia'),
        ('wikimedia.org', 'Wikimedia content'),
        ('wikibooks.org', 'Wikibooks'),
    ]

    # Gaming - Young (Harriet)
    harriet_gaming = [
        ('nickjr.com', 'Nick Jr games'),
        ('pbskids.org', 'PBS Kids games'),
        ('lego.com', 'LEGO games and activities'),
    ]

    # Gaming - Older (Aurora)
    aurora_gaming = [
        ('minecraft.net', 'Minecraft'),
        ('mojang.com', 'Mojang (Minecraft)'),
        ('roblox.com', 'Roblox'),
        ('rbxcdn.com', 'Roblox CDN'),
        ('lego.com', 'LEGO'),
    ]

    # Add domains to Harriet's profile
    print(f"\n🎀 Adding domains to Harriet's profile...")
    harriet_count = 0

    for domain, desc in essential_domains + streaming_domains + harriet_educational + harriet_gaming:
        if add_to_profile_whitelist(harriet_id, domain, desc, 'admin'):
            harriet_count += 1

    print(f"   ✓ Added {harriet_count} domains")

    # Add domains to Aurora's profile
    print(f"\n💜 Adding domains to Aurora's profile...")
    aurora_count = 0

    for domain, desc in essential_domains + streaming_domains + aurora_educational + aurora_gaming:
        if add_to_profile_whitelist(aurora_id, domain, desc, 'admin'):
            aurora_count += 1

    print(f"   ✓ Added {aurora_count} domains")

    # Display summary
    print("\n" + "=" * 60)
    print("✅ Initialization Complete!")
    print("=" * 60)

    harriet = get_profile(harriet_id)
    aurora = get_profile(aurora_id)

    print(f"\n📋 Harriet's Profile:")
    print(f"   Age: {harriet['age']}")
    print(f"   Color: {harriet['color']}")
    print(f"   Whitelisted domains: {harriet_count}")
    print(f"   Categories: Essential, Streaming, Young Educational, Young Gaming")

    print(f"\n📋 Aurora's Profile:")
    print(f"   Age: {aurora['age']}")
    print(f"   Color: {aurora['color']}")
    print(f"   Whitelisted domains: {aurora_count}")
    print(f"   Categories: Essential, Streaming, Advanced Educational, Gaming")

    print("\n📱 Next Steps:")
    print("   1. Assign devices to profiles in the web UI")
    print("   2. Monitor DNS logs to see what domains are being requested")
    print("   3. Add additional domains as needed via the web interface")
    print("   4. View dashboard: http://localhost:8080")
    print("\n")


if __name__ == '__main__':
    initialize_profiles()
