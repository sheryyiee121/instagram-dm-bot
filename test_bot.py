#!/usr/bin/env python3
"""
Test script to debug bot startup issues
"""

import sys
import os

# Add the backend/src directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_path)

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import flask
        print("✓ Flask imported successfully")
    except ImportError as e:
        print(f"✗ Flask import failed: {e}")
        return False
    
    try:
        import instagrapi
        print("✓ Instagrapi imported successfully")
    except ImportError as e:
        print(f"✗ Instagrapi import failed: {e}")
        return False
    
    try:
        import selenium
        print("✓ Selenium imported successfully")
    except ImportError as e:
        print(f"✗ Selenium import failed: {e}")
        return False
    
    try:
        from database import db
        print("✓ Database module imported successfully")
    except ImportError as e:
        print(f"✗ Database import failed: {e}")
        return False
    
    try:
        from instadm import InstaDM
        print("✓ InstaDM imported successfully")
    except ImportError as e:
        print(f"✗ InstaDM import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database initialization"""
    print("\nTesting database...")
    
    try:
        from database import db
        print("✓ Database initialized successfully")
        
        # Test basic operations
        accounts = db.get_accounts()
        print(f"✓ Found {len(accounts)} accounts in database")
        
        usernames = db.get_unprocessed_usernames()
        print(f"✓ Found {len(usernames)} unprocessed usernames")
        
        analytics = db.get_analytics()
        print(f"✓ Analytics: {analytics}")
        
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_flask_app():
    """Test Flask app creation"""
    print("\nTesting Flask app...")
    
    try:
        from run import app
        print("✓ Flask app created successfully")
        return True
    except Exception as e:
        print(f"✗ Flask app creation failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔍 Testing Instagram DM Bot...")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Please install missing packages:")
        print("pip install flask instagrapi selenium webdriver-manager")
        return
    
    # Test database
    if not test_database():
        print("\n❌ Database tests failed.")
        return
    
    # Test Flask app
    if not test_flask_app():
        print("\n❌ Flask app tests failed.")
        return
    
    print("\n✅ All tests passed! The bot should work correctly.")
    print("\nTo start the bot, run:")
    print("python backend/src/run.py")

if __name__ == "__main__":
    main() 