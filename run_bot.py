#!/usr/bin/env python3
"""
Main entry point for the Instagram DM Bot
"""

import os
import sys
import json
from flask import request, jsonify

# Add the backend/src directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_path)

def main():
    """Main function to run the bot"""
    print("🚀 Starting Instagram DM Bot...")
    print("📁 Make sure you have configured your accounts in infos/accounts.json")
    print("📝 Make sure you have target usernames in infos/usernames.txt")
    print("💬 Make sure you have your message in infos/messages.json")
    print("\n🌐 Starting web interface at http://localhost:5000")
    print("📊 You can control the bot through the web interface")
    print("⏹️  Press Ctrl+C to stop the bot\n")
    
    try:
        from run import app
        app.route('/api/accounts/proxy', methods=['POST'])(set_account_proxy)
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)

@app.route('/api/accounts/proxy', methods=['POST'])
def set_account_proxy():
    data = request.get_json()
    username = data['username']
    proxy = data['proxy']
    for account in accounts:
        if account['username'] == username:
            account['proxy'] = proxy
            break
    # Save to file
    with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(accounts, f, indent=2)
    return jsonify({'status': 'success'})

if __name__ == "__main__":
    main() 