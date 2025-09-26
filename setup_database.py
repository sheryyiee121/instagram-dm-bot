#!/usr/bin/env python3
"""
Setup script to initialize the database with test data
"""

import sys
import os

# Add the backend/src directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_path)

from database import db

def setup_test_data():
    """Add some test data to the database"""
    print("Setting up test data...")
    
    # Add a test account
    print("Adding test account...")
    db.save_account("test_user", "test_password")
    
    # Add some test usernames
    print("Adding test usernames...")
    test_usernames = [
        "sherry_iee",
        "test_user1", 
        "test_user2",
        "test_user3",
        "test_user4"
    ]
    
    test_firstnames = {
        "sherry_iee": "Sherry",
        "test_user1": "John",
        "test_user2": "Jane", 
        "test_user3": "Mike",
        "test_user4": "Sarah"
    }
    
    db.save_usernames(test_usernames, test_firstnames)
    
    print("✓ Test data added successfully!")
    print(f"✓ Added 1 test account")
    print(f"✓ Added {len(test_usernames)} test usernames")
    
    # Show current database state
    accounts = db.get_accounts()
    usernames = db.get_unprocessed_usernames()
    analytics = db.get_analytics()
    
    print(f"\n📊 Current Database State:")
    print(f"   Accounts: {len(accounts)}")
    print(f"   Unprocessed usernames: {len(usernames)}")
    print(f"   Analytics: {analytics}")

def main():
    """Main setup function"""
    print("🔧 Setting up Instagram DM Bot Database...")
    print("=" * 50)
    
    try:
        setup_test_data()
        print("\n✅ Database setup complete!")
        print("\nYou can now:")
        print("1. Start the bot: python backend/src/run.py")
        print("2. Open the web interface: http://localhost:5000")
        print("3. Replace test data with your real accounts and usernames")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main() 