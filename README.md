# Instagram DM Bot

An automated Instagram Direct Message sender with web interface control.

## Features

- 🤖 Automated DM sending to multiple users
- 🌐 Web interface for easy control
- 🔄 Session management and reuse
- 📊 Real-time logging and status
- 🎯 Personalized messages with firstname replacement
- 🔒 Secure session storage
- ⚡ Multi-account support
- 🛡️ Anti-detection measures

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Your Accounts

Edit `infos/accounts.json`:
```json
[
  {
    "username": "your_instagram_username",
    "password": "your_instagram_password"
  }
]
```

### 3. Add Target Usernames

Edit `infos/usernames.txt`:
```
target_user1
target_user2
target_user3
```

### 4. Customize Your Message

Edit `infos/messages.json`:
```json
{
  "message": "Hey <FIRSTNAME>! I love your content. Let's connect! 😊"
}
```

### 5. Add Firstnames (Optional)

Edit `infos/firstnames.json`:
```json
{
  "target_user1": "John",
  "target_user2": "Sarah"
}
```

## Usage

### Start the Bot

```bash
python run_bot.py
```

### Access Web Interface

Open your browser and go to: `http://localhost:5000`

### Web Interface Features

- **Start/Stop Bot**: Control the bot execution
- **Real-time Logs**: See what the bot is doing
- **Status Monitoring**: Check bot status and progress
- **Configuration Reload**: Reload settings without restart

## How It Works

1. **Session Management**: The bot uses Selenium to log in and saves sessions for reuse
2. **Anti-Detection**: Implements human-like typing delays and browser fingerprinting
3. **Rate Limiting**: Random delays between messages (15-30 seconds)
4. **Account Rotation**: Switches accounts after 25 messages per account
5. **Error Handling**: Automatic retry and session refresh on failures

## Safety Features

- ✅ Random delays between messages
- ✅ Human-like typing patterns
- ✅ Session reuse to avoid frequent logins
- ✅ Account rotation to prevent rate limiting
- ✅ Error handling and retry logic
- ✅ Anti-detection browser settings

## File Structure

```
100kbit/
├── backend/src/
│   ├── run.py          # Main Flask application
│   ├── instadm.py      # Instagram DM automation
│   └── __init__.py
├── infos/
│   ├── accounts.json   # Instagram accounts
│   ├── usernames.txt   # Target usernames
│   ├── messages.json   # DM message template
│   └── firstnames.json # Username to firstname mapping
├── templates/
│   └── index.html      # Web interface
├── requirements.txt    # Python dependencies
├── run_bot.py         # Main entry point
└── wsgi.py           # WSGI configuration
```

## Important Notes

⚠️ **Use Responsibly**: 
- Respect Instagram's terms of service
- Don't spam users
- Use reasonable delays between messages
- Monitor your accounts for any restrictions

🔧 **Troubleshooting**:
- If login fails, check your credentials
- If 2FA is enabled, enter the code manually when prompted
- Clear session files if you encounter persistent login issues
- Check logs for detailed error messages

## API Endpoints

- `GET /` - Web interface
- `GET /bot-status` - Get bot status
- `GET /get-logs` - Get recent logs
- `POST /run-bot` - Start the bot
- `POST /stop-bot` - Stop the bot
- `POST /reload-config` - Reload configuration

## License

This project is for educational purposes. Use at your own risk. 