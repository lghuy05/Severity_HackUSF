#!/usr/bin/env python3
"""Test Firebase connection"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.firebase_client import init_firebase, get_hospitals

try:
    print("Initializing Firebase...")
    db = init_firebase()
    print("✓ Firebase initialized successfully")
    
    print("\nFetching hospitals from Firestore...")
    hospitals = get_hospitals()
    
    if hospitals:
        print(f"✓ Found {len(hospitals)} hospitals:")
        for h in hospitals[:3]:
            print(f"  - {h.get('name', 'Unknown')} at {h.get('location', 'Unknown location')}")
    else:
        print("⚠ No hospitals found (collection might be empty)")
    
    print("\n✓ Firebase connection working!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
