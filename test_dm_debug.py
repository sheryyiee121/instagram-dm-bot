#!/usr/bin/env python3
"""
Debug script to test DM sending and identify specific errors
"""

import sys
import os
import json

# Add the backend/src directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_path)

from instadm import InstaDM

def test_dm_sending():
    """Test DM sending with detailed error reporting"""
    
    # Load configuration
    config_dir = os.path.join(os.path.dirname(__file__), "infos")
    accounts_file = os.path.join(config_dir, "accounts.json")
    usernames_file = os.path.join(config_dir, "usernames.txt")
    messages_file = os.path.join(config_dir, "messages.json")
    
    try:
        # Load account
        with open(accounts_file, 'r', encoding='utf-8') as f:
            accounts = json.load(f)
        
        if not accounts:
            print("❌ No accounts found in accounts.json")
            return
        
        account = accounts[0]  # Use first account
        print(f"🔐 Testing with account: {account['username']}")
        
        # Load usernames
        with open(usernames_file, 'r', encoding='utf-8') as f:
            usernames = [line.strip() for line in f.readlines() if line.strip()]
        
        if not usernames:
            print("❌ No usernames found in usernames.txt")
            return
        
        test_username = usernames[0]  # Test with first username
        print(f"👤 Testing DM to: {test_username}")
        
        # Load message
        with open(messages_file, 'r', encoding='utf-8') as f:
            message_data = json.load(f)
            message_text = message_data.get("message", "Hello! How are you?")
        
        print(f"💬 Message: {message_text[:50]}...")
        
        # Initialize InstaDM
        session_file = f"session_{account['username']}.json"
        print(f"📁 Session file: {session_file}")
        
        try:
            insta = InstaDM(username=account["username"], password=account["password"], session_file=session_file)
            print("✅ Login successful!")
            
            # Test getting user ID first
            print(f"🔍 Getting user ID for {test_username}...")
            try:
                user_id = insta.client.user_id_from_username(test_username)
                print(f"✅ User ID found: {user_id}")
            except Exception as e:
                print(f"❌ Failed to get user ID: {e}")
                print("Possible reasons:")
                print("  - Username doesn't exist")
                print("  - Instagram blocked the request")
                print("  - Network issues")
                print("  - Rate limiting")
                return
            
            # Test sending DM
            print(f"📤 Sending DM to {test_username}...")
            success, error = insta.send_dm(userdm=test_username, messageText=message_text)
            
            if success:
                print("✅ DM sent successfully!")
            else:
                print(f"❌ Failed to send DM: {error}")
                print("\nPossible reasons:")
                print("  - User has DMs disabled")
                print("  - You're not following the user (and they have DMs restricted)")
                print("  - Instagram blocked the DM")
                print("  - Rate limiting")
                print("  - Account restrictions")
                print("  - User doesn't exist")
                print("  - Network issues")
            
            insta.logout()
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            print("Possible reasons:")
            print("  - Wrong username/password")
            print("  - Account is locked/suspended")
            print("  - 2FA required")
            print("  - Instagram security check")
            print("  - Network issues")
    
    except FileNotFoundError as e:
        print(f"❌ Configuration file not found: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🔍 Instagram DM Debug Tool")
    print("=" * 40)
    test_dm_sending() 