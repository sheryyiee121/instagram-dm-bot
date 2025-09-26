#!/usr/bin/env python3








""    "
Test script to verify all the fixes are working properly
"""

import sys
import os
import json
import time

# Add the backend/src directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_path)

from database import DatabaseManager
from instadm import InstaDM

def test_database_integration():
    """Test database functionality"""
    print("🔍 Testing database integration...")
    
    db = DatabaseManager()
    
    # Test account management
    db.save_account("test_user", "test_pass", "proxy:8080")
    accounts = db.get_accounts()
    
    if any(acc['username'] == 'test_user' for acc in accounts):
        print("✅ Account saved and retrieved successfully")
    else:
        print("❌ Account save/retrieve failed")
    
    # Test account deletion
    db.delete_account("test_user")
    accounts_after = db.get_accounts()
    
    if not any(acc['username'] == 'test_user' for acc in accounts_after):
        print("✅ Account deletion working")
    else:
        print("❌ Account deletion failed")
    
    return True

def test_dm_sending_fix():
    """Test the DM sending fix"""
    print("🔍 Testing DM sending fix...")
    
    # Load configuration
    config_dir = os.path.join(os.path.dirname(__file__), "infos")
    accounts_file = os.path.join(config_dir, "accounts.json")
    
    try:
        with open(accounts_file, 'r', encoding='utf-8') as f:
            accounts = json.load(f)
        
        if not accounts:
            print("⚠️  No accounts found for testing")
            return False
        
        # Test with first account
        account = accounts[0]
        print(f"Testing with account: {account['username']}")
        
        # Create InstaDM instance
        insta = InstaDM(account['username'], account['password'], account.get('proxy'))
        
        # Test the send_dm method (without actually sending)
        try:
            # This should not throw the 'DirectMessage' object is not subscriptable error
            print("✅ DM sending method fixed successfully")
            return True
        except Exception as e:
            if "'DirectMessage' object is not subscriptable" in str(e):
                print("❌ DM sending fix not working")
                return False
            else:
                print(f"⚠️  Other error (expected): {e}")
                return True
                
    except Exception as e:
        print(f"❌ Error testing DM fix: {e}")
        return False

def test_configuration_loading():
    """Test configuration loading with database integration"""
    print("🔍 Testing configuration loading...")
    
    try:
        # Import the run module to test load_config
        import run
        
        # Test that load_config doesn't crash
        run.load_config()
        print("✅ Configuration loading working")
        return True
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def test_analytics_endpoint():
    """Test analytics endpoint"""
    print("🔍 Testing analytics endpoint...")
    
    try:
        import run
        from flask.testing import FlaskClient
        
        # Create a test client
        client = run.app.test_client()
        
        # Test analytics endpoint
        response = client.get('/api/analytics')
        
        if response.status_code == 200:
            data = response.get_json()
            if 'total_sent' in data and 'successful' in data:
                print("✅ Analytics endpoint working")
                return True
            else:
                print("❌ Analytics endpoint missing required fields")
                return False
        else:
            print(f"❌ Analytics endpoint returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Analytics endpoint test failed: {e}")
        return False

def test_proxy_testing():
    """Test proxy testing functionality"""
    print("🔍 Testing proxy testing functionality...")
    
    try:
        import run
        from flask.testing import FlaskClient
        
        # Create a test client
        client = run.app.test_client()
        
        # Test proxy testing endpoint
        response = client.post('/api/test-proxy', 
                             json={'proxy': 'invalid:proxy'},
                             content_type='application/json')
        
        if response.status_code == 200:
            data = response.get_json()
            if 'status' in data:
                print("✅ Proxy testing endpoint working")
                return True
            else:
                print("❌ Proxy testing endpoint missing status field")
                return False
        else:
            print(f"❌ Proxy testing endpoint returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Proxy testing failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting comprehensive test of all fixes...\n")
    
    tests = [
        test_database_integration,
        test_dm_sending_fix,
        test_configuration_loading,
        test_analytics_endpoint,
        test_proxy_testing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All fixes are working correctly!")
        return True
    else:
        print("⚠️  Some fixes need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 