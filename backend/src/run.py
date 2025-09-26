from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json
import random
import time
import logging
import os
import threading
import datetime
from instadm import InstaDM, read_usernames, read_firstnames_json, read_accounts_json
from database import DatabaseManager

app = Flask(__name__, template_folder='../../templates')
CORS(app)  # Enable CORS for all routes

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Bot status and data
bot_running = False
bot_thread = None
sent_usernames = set()
current_logs = []

# Initialize database
db = DatabaseManager()

# Configuration paths - Use absolute path to ensure consistency
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "infos")
ACCOUNTS_FILE = os.path.join(CONFIG_DIR, "accounts.json")
USERNAMES_FILE = os.path.join(CONFIG_DIR, "usernames.txt")
MESSAGE_FILE = os.path.join(CONFIG_DIR, "messages.json")
FIRSTNAMES_FILE = os.path.join(CONFIG_DIR, "firstnames.json")
DM_SETTINGS_FILE = os.path.join(CONFIG_DIR, "dm_settings.json")

def load_config():
    """Load configuration files with error handling"""
    global accounts, usernames, message_text, firstnames
    
    # Debug: Log the CONFIG_DIR path
    add_log(f"CONFIG_DIR: {CONFIG_DIR}")
    add_log(f"CONFIG_DIR exists: {os.path.exists(CONFIG_DIR)}")
    
    try:
        # Load accounts from database first, then fallback to file
        db_accounts = db.get_accounts()
        if db_accounts:
            accounts = db_accounts
            add_log(f"Loaded {len(accounts)} accounts from database")
        else:
            # Fallback to file
            if os.path.exists(ACCOUNTS_FILE):
                with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                    accounts = json.load(f)
                # Save to database
                for account in accounts:
                    db.save_account(account['username'], account['password'], account.get('proxy'))
            else:
                # Create default accounts file
                accounts = [
                    {"username": "your_username", "password": "your_password"}
                ]
                with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
                    json.dump(accounts, f, indent=2)
        
        # Load usernames
        usernames = read_usernames(USERNAMES_FILE) if os.path.exists(USERNAMES_FILE) else []
        
        # Load messages
        if os.path.exists(MESSAGE_FILE):
            with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
                message_data = json.load(f)
                message_text = message_data.get("message", "Hello! How are you?")
        else:
            message_text = "Hello! How are you?"
        
        # Load firstnames
        firstnames = read_firstnames_json(FIRSTNAMES_FILE) if os.path.exists(FIRSTNAMES_FILE) else {}
        
        add_log(f"Configuration loaded: {len(accounts)} accounts, {len(usernames)} usernames")
        
    except Exception as e:
        add_log(f"Error loading configuration: {e}")
        accounts = []
        usernames = []
        message_text = "Hello! How are you?"
        firstnames = {}

def add_log(message):
    """Add log message to current logs"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    current_logs.append(log_entry)
    if len(current_logs) > 100:  # Keep only last 100 logs
        current_logs.pop(0)
    logging.info(message)

def load_dm_settings():
    # Load DM settings from file or set defaults
    defaults = {
        'total_dms': 100,
        'dms_per_account': 25,
        'auto_engage': True,  # Enable auto-engagement by default
        'auto_like': True,    # Auto like posts
        'auto_story': True,   # Auto watch stories
        'auto_comment': False, # Auto comment (disabled by default)
        'auto_follow': False,  # Auto follow (disabled by default)
        'delay_between_dms': 20,
        'delay_between_accounts': 2,
        'use_browser_mode': True  # New setting for browser visibility
    }
    if os.path.exists(DM_SETTINGS_FILE):
        try:
            with open(DM_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            for k, v in defaults.items():
                if k not in settings:
                    settings[k] = v
            return settings
        except Exception as e:
            add_log(f"Error loading DM settings: {e}")
            return defaults
    else:
        return defaults

def save_dm_settings(settings):
    try:
        with open(DM_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        add_log(f"Error saving DM settings: {e}")
        return False

def dm_bot_worker():
    global bot_running, sent_usernames
    add_log("Starting DM bot worker...")
    settings = load_dm_settings()
    total_dms = settings.get('total_dms', 100)
    dms_per_account = settings.get('dms_per_account', 25)
    delay_between_dms = settings.get('delay_between_dms', 20)
    delay_between_accounts = settings.get('delay_between_accounts', 2)
    use_browser_mode = settings.get('use_browser_mode', True)
    total_sent = 0
    try:
        for account in accounts:
            if not bot_running or total_sent >= total_dms:
                break
            if not usernames:
                add_log("No more usernames to process")
                break
            add_log(f"Starting DM process with account: {account['username']}")
            session_file = f"session_{account['username']}.json"
            try:
                # Use browser mode based on settings
                if use_browser_mode:
                    add_log(f"🌐 Using HYBRID MODE for {account['username']} - Browser login → API DM sending")
                else:
                    add_log(f"🔧 Using API MODE for {account['username']} - Direct API login & DM sending")
                insta = InstaDM(username=account["username"], password=account["password"], session_file=session_file, use_browser=use_browser_mode)
                add_log(f"Successfully logged in with {account['username']}")
                messages_sent = 0
                while usernames and messages_sent < dms_per_account and bot_running and total_sent < total_dms:
                    username = usernames.pop(0)
                    if username in sent_usernames:
                        add_log(f"Skipping already sent username: {username}")
                        continue
                    firstname = firstnames.get(username, "Friend")
                    personalized_message = message_text.replace("<FIRSTNAME>", firstname)
                    add_log(f"Sending to {username} (firstname: {firstname})")
                    
                    # Pass engagement settings
                    engagement_settings = {
                        'auto_engage': settings.get('auto_engage', True),
                        'auto_like': settings.get('auto_like', True),
                        'auto_story': settings.get('auto_story', True),
                        'auto_comment': settings.get('auto_comment', False),
                        'auto_follow': settings.get('auto_follow', False)
                    }
                    success, error = insta.send_dm(userdm=username, messageText=personalized_message, engagement_settings=engagement_settings)
                    if success:
                        sent_usernames.add(username)
                        messages_sent += 1
                        total_sent += 1
                        add_log(f"✓ Sent {messages_sent}/{dms_per_account} messages with {account['username']} to {username}")
                    else:
                        add_log(f"✗ Failed to send to {username}: {error}")
                        usernames.append(username)
                        continue
                    # Use delay from settings
                    delay = delay_between_dms
                    add_log(f"Waiting {delay} seconds before next message...")
                    time.sleep(delay)
                if messages_sent == dms_per_account:
                    add_log(f"Reached {dms_per_account} messages with {account['username']}. Switching account.")
                insta.logout()
            except Exception as e:
                add_log(f"Error with account {account['username']}: {e}")
                continue
            # Delay between account switches
            if bot_running and len(accounts) > 1 and total_sent < total_dms:
                delay = delay_between_accounts * 60
                add_log(f"Switching accounts in {delay} seconds...")
                time.sleep(delay)
        add_log("DM bot worker finished")
    except Exception as e:
        add_log(f"Critical error in DM bot worker: {e}")
    finally:
        bot_running = False

# Load configuration on startup
load_config()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/old')
def old_index():
    dm_settings = {
        'total_dms': 25,
        'dms_per_account': 25
    }
    return render_template('index.html', dm_settings=dm_settings)

@app.route('/bot-status', methods=['GET'])
def bot_status():
    return jsonify({
        "running": bot_running,
        "accounts_count": len(accounts),
        "usernames_remaining": len(usernames),
        "sent_count": len(sent_usernames)
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "OK",
        "message": "Server is running",
        "timestamp": time.time()
    })

@app.route('/get-logs', methods=['GET'])
def get_logs():
    return jsonify({"logs": current_logs})

@app.route('/run-bot', methods=['POST'])
def run_bot():
    global bot_running, bot_thread
    
    # Add debugging information
    add_log(f"POST request received to /run-bot")
    add_log(f"Request method: {request.method}")
    add_log(f"Request headers: {dict(request.headers)}")
    add_log(f"Request data: {request.get_data()}")
    
    if bot_running:
        add_log("Bot is already running - returning 400")
        return jsonify({"status": "Bot is already running"}), 400

    if not accounts:
        add_log("No accounts configured - returning 400")
        return jsonify({"status": "Error", "error": "No accounts configured"}), 400
        
    if not usernames:
        add_log("No usernames to send DMs to - returning 400")
        return jsonify({"status": "Error", "error": "No usernames to send DMs to"}), 400

    bot_running = True
    bot_thread = threading.Thread(target=dm_bot_worker, daemon=True)
    bot_thread.start()
    
    add_log("Bot started successfully")
    return jsonify({"status": "Bot started"}), 200

@app.route('/stop-bot', methods=['POST'])
def stop_bot():
    global bot_running
    
    if not bot_running:
        return jsonify({"status": "Bot is not running"}), 400

    bot_running = False
    add_log("Bot stop requested")
    return jsonify({"status": "Bot stop requested"}), 200

@app.route('/reload-config', methods=['POST'])
def reload_config():
    global accounts, usernames, message_text, firstnames
    
    load_config()
    add_log("Configuration reloaded")
    return jsonify({"status": "Configuration reloaded"}), 200

# New API endpoints for dashboard
@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """Get all accounts with their status"""
    account_status = []
    for account in accounts:
        account_status.append({
            'username': account['username'],
            'active': True,
            'status': 'ready',
            'sent': 0,
            'limit': 25
        })
    return jsonify({'accounts': account_status})

@app.route('/api/accounts', methods=['POST'])
def add_account():
    """Add a new account"""
    data = request.get_json()
    new_account = {
        'username': data['username'],
        'password': data['password'],
        'proxy': data.get('proxy')
    }
    
    # Save to database
    try:
        db.save_account(data['username'], data['password'], data.get('proxy'))
        accounts.append(new_account)
        add_log(f"Account {data['username']} added successfully")
        return jsonify({'status': 'success', 'message': 'Account added'}), 200
    except Exception as e:
        add_log(f"Error saving account: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/accounts/<username>', methods=['DELETE'])
def delete_account(username):
    """Delete an account"""
    try:
        # Remove from database
        db.delete_account(username)
        
        # Remove from memory
        global accounts
        accounts = [acc for acc in accounts if acc['username'] != username]
        
        # Delete session if exists
        db.delete_session(username)
        
        add_log(f"Account {username} deleted successfully")
        return jsonify({'status': 'success', 'message': 'Account deleted'}), 200
    except Exception as e:
        add_log(f"Error deleting account: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/settings', methods=['GET'])
def get_settings():
    settings = load_dm_settings()
    settings['message'] = message_text
    return jsonify(settings)

@app.route('/api/settings', methods=['POST'])
def update_settings():
    global message_text
    data = request.get_json()
    # Update message
    message_text = data.get('message', message_text)
    # Save message to file
    try:
        add_log(f"Attempting to save message to: {MESSAGE_FILE}")
        add_log(f"Message file exists: {os.path.exists(MESSAGE_FILE)}")
        add_log(f"Directory exists: {os.path.exists(os.path.dirname(MESSAGE_FILE))}")
        
        with open(MESSAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'message': message_text}, f, indent=2)
        add_log("Message text updated via settings API.")
    except Exception as e:
        add_log(f"Error saving message to {MESSAGE_FILE}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    # Save DM settings
    dm_settings = {
        'total_dms': int(data.get('total_dms', 100)),
        'dms_per_account': int(data.get('dms_per_account', 25)),
        'delay_between_dms': int(data.get('delay_between_dms', 20)),
        'delay_between_accounts': int(data.get('delay_between_accounts', 2)),
        'use_browser_mode': bool(data.get('use_browser_mode', True))
    }
    if save_dm_settings(dm_settings):
        add_log("Settings updated successfully")
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Failed to save settings'}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data"""
    try:
        # Get database analytics
        db_analytics = db.get_analytics()
        
        analytics = {
            'total_sent': len(sent_usernames),
            'successful': len(sent_usernames),
            'failed': db_analytics.get('failed_dms', 0),
            'remaining': len(usernames),
            'accounts_count': len(accounts),
            'usernames_remaining': len(usernames),
            'today_sent': db_analytics.get('today_sent', 0),
            'total_dms_sent': db_analytics.get('total_dms_sent', 0),
            'campaign_stats': {
                'started_at': db_analytics.get('campaign_started', ''),
                'dms_per_hour': db_analytics.get('dms_per_hour', 0),
                'success_rate': db_analytics.get('success_rate', 0)
            }
        }
        return jsonify(analytics)
    except Exception as e:
        add_log(f"Error getting analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-proxy', methods=['POST'])
def test_proxy():
    """Test if proxy is working"""
    data = request.get_json()
    proxy = data.get('proxy')
    
    if not proxy:
        return jsonify({'status': 'error', 'message': 'No proxy provided'}), 400
    
    try:
        import requests
        from requests.exceptions import RequestException
        
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        # Test with a simple request
        response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
        
        if response.status_code == 200:
            ip_info = response.json()
            return jsonify({
                'status': 'success',
                'message': 'Proxy is working',
                'ip': ip_info.get('origin', 'Unknown'),
                'response_time': response.elapsed.total_seconds()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Proxy test failed with status {response.status_code}'
            })
            
    except RequestException as e:
        return jsonify({
            'status': 'error',
            'message': f'Proxy test failed: {str(e)}'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        })

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

@app.route('/api/upload_usernames', methods=['POST'])
def upload_usernames():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    try:
        content = file.read().decode('utf-8')
        usernames = [line.strip() for line in content.splitlines() if line.strip()]
        
        # Debug logging
        add_log(f"Attempting to save usernames to: {USERNAMES_FILE}")
        add_log(f"Usernames file exists: {os.path.exists(USERNAMES_FILE)}")
        add_log(f"Directory exists: {os.path.exists(os.path.dirname(USERNAMES_FILE))}")
        
        # Save to usernames.txt
        with open(USERNAMES_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(usernames))
        # Reload config to update in-memory list
        load_config()
        add_log(f"Usernames updated via upload API. {len(usernames)} usernames loaded.")
        return jsonify({'success': True})
    except Exception as e:
        add_log(f"Error uploading usernames: {e}")
        return jsonify({'success': False, 'message': str(e)})

# Engagement Feature API Endpoints
@app.route('/api/engagement/like', methods=['POST'])
def like_post():
    """Like a post"""
    data = request.get_json()
    username = data.get('username')
    post_url = data.get('post_url')
    
    if not username or not post_url:
        return jsonify({'status': 'error', 'message': 'Username and post URL required'}), 400
    
    try:
        # Find the account
        account = None
        for acc in accounts:
            if acc['username'] == username:
                account = acc
                break
        
        if not account:
            return jsonify({'status': 'error', 'message': 'Account not found'}), 404
        
        # Create InstaDM instance
        bot = InstaDM(account['username'], account['password'], use_browser=False)
        
        # Like the post
        success, error = bot.like_post(post_url)
        
        if success:
            add_log(f"{username} liked post: {post_url}")
            return jsonify({'status': 'success', 'message': 'Post liked successfully'})
        else:
            add_log(f"Failed to like post for {username}: {error}")
            return jsonify({'status': 'error', 'message': error}), 500
            
    except Exception as e:
        add_log(f"Error in like endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/engagement/comment', methods=['POST'])
def comment_post():
    """Comment on a post"""
    data = request.get_json()
    username = data.get('username')
    post_url = data.get('post_url')
    comment_text = data.get('comment_text')
    
    if not username or not post_url or not comment_text:
        return jsonify({'status': 'error', 'message': 'Username, post URL, and comment required'}), 400
    
    try:
        # Find the account
        account = None
        for acc in accounts:
            if acc['username'] == username:
                account = acc
                break
        
        if not account:
            return jsonify({'status': 'error', 'message': 'Account not found'}), 404
        
        # Create InstaDM instance
        bot = InstaDM(account['username'], account['password'], use_browser=False)
        
        # Comment on the post
        success, error = bot.comment_post(post_url, comment_text)
        
        if success:
            add_log(f"{username} commented on post: {post_url}")
            return jsonify({'status': 'success', 'message': 'Comment posted successfully'})
        else:
            add_log(f"Failed to comment for {username}: {error}")
            return jsonify({'status': 'error', 'message': error}), 500
            
    except Exception as e:
        add_log(f"Error in comment endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/engagement/story', methods=['POST'])
def watch_story():
    """Watch a user's story"""
    data = request.get_json()
    username = data.get('username')
    target_username = data.get('target_username')
    
    if not username or not target_username:
        return jsonify({'status': 'error', 'message': 'Username and target username required'}), 400
    
    try:
        # Find the account
        account = None
        for acc in accounts:
            if acc['username'] == username:
                account = acc
                break
        
        if not account:
            return jsonify({'status': 'error', 'message': 'Account not found'}), 404
        
        # Create InstaDM instance
        bot = InstaDM(account['username'], account['password'], use_browser=False)
        
        # Watch the story
        success, message = bot.watch_story(target_username)
        
        if success:
            add_log(f"{username} watched stories from: {target_username}")
            return jsonify({'status': 'success', 'message': message})
        else:
            add_log(f"Failed to watch stories for {username}: {message}")
            return jsonify({'status': 'error', 'message': message}), 500
            
    except Exception as e:
        add_log(f"Error in story endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/engagement/follow', methods=['POST'])
def follow_user():
    """Follow a user"""
    data = request.get_json()
    username = data.get('username')
    target_username = data.get('target_username')
    
    if not username or not target_username:
        return jsonify({'status': 'error', 'message': 'Username and target username required'}), 400
    
    try:
        # Find the account
        account = None
        for acc in accounts:
            if acc['username'] == username:
                account = acc
                break
        
        if not account:
            return jsonify({'status': 'error', 'message': 'Account not found'}), 404
        
        # Create InstaDM instance
        bot = InstaDM(account['username'], account['password'], use_browser=False)
        
        # Follow the user
        success, error = bot.follow_user(target_username)
        
        if success:
            add_log(f"{username} followed: {target_username}")
            return jsonify({'status': 'success', 'message': 'User followed successfully'})
        else:
            add_log(f"Failed to follow for {username}: {error}")
            return jsonify({'status': 'error', 'message': error}), 500
            
    except Exception as e:
        add_log(f"Error in follow endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/engagement/stats', methods=['GET'])
def get_engagement_stats():
    """Get engagement statistics for all accounts"""
    try:
        stats = {}
        for account in accounts:
            account_stats = db.get_engagement_stats(account['username'])
            recent_activities = db.get_recent_engagements(account['username'], limit=10)
            stats[account['username']] = {
                'daily_stats': account_stats,
                'recent_activities': recent_activities
            }
        
        return jsonify({'status': 'success', 'stats': stats})
        
    except Exception as e:
        add_log(f"Error getting engagement stats: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)