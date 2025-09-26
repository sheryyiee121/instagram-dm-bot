import json
import random
import time
import logging
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from instagrapi import Client
from database import db  # <-- Import the database manager

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class color:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET_ALL = "\033[0m"
    BLUE = "\033[96m"

def read_usernames(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            usernames = [line.strip() for line in f.readlines() if line.strip()]
        logging.debug(f"Read usernames: {usernames}")
        return usernames
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return []
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return []

def read_accounts_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            accounts = json.load(f)
        logging.info(f"Loaded accounts from JSON: {accounts}")
        return accounts
    except FileNotFoundError:
        logging.error(f"Accounts JSON file not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON in {file_path}: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error reading accounts JSON file {file_path}: {e}")
        return {}

def read_firstnames_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            firstnames = json.load(f)
        logging.info(f"Loaded firstnames from JSON: {len(firstnames)} entries")
        return firstnames
    except FileNotFoundError:
        logging.warning(f"Firstnames JSON file not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON in {file_path}: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error reading firstnames JSON file {file_path}: {e}")
        return {}

def selenium_login(username, password, session_file):
    """Enhanced Selenium login with better session management"""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        logging.info(f"Starting Selenium login for {username}")
        driver.get("https://www.instagram.com")
        time.sleep(random.uniform(3, 6))

        # Wait for login form and fill credentials
        username_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = driver.find_element(By.NAME, "password")
        
        # Type credentials with human-like delays
        for char in username:
            username_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        
        time.sleep(random.uniform(0.5, 1.5))
        
        for char in password:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        
        time.sleep(random.uniform(0.5, 1.5))
        
        # Click login button
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        # Handle 2FA/Challenge if needed
        try:
            verification_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, "verificationCode"))
            )
            logging.info(f"2FA/Challenge required for {username}. Please enter the code manually in the browser.")
            print(f"{color.YELLOW}2FA/Challenge required for {username}. Please enter the code in the opened browser window.{color.RESET_ALL}")
            
            # Wait for successful login after 2FA
            WebDriverWait(driver, 300).until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, "//a[@href='/']")),
                    EC.presence_of_element_located((By.XPATH, "//a[@href='/explore/']")),
                    EC.presence_of_element_located((By.XPATH, "//a[@href='/reels/']")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(@aria-label, 'Profile')]"))
                )
            )
            logging.info(f"2FA/Challenge completed successfully for {username}")
            
        except Exception:
            logging.info(f"No 2FA/Challenge required or already handled for {username}")

        # Handle "Save Info" prompt
        try:
            save_info_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Save Info']"))
            )
            save_info_button.click()
            logging.info("Clicked 'Save Info' button")
        except Exception:
            logging.info("No 'Save Info' prompt found or already handled")

        # Handle "Turn on Notifications" prompt
        try:
            not_now_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Not Now']"))
            )
            not_now_button.click()
            logging.info("Clicked 'Not Now' for notifications")
        except Exception:
            logging.info("No notification prompt found or already handled")

        # Verify successful login with multiple selectors
        try:
            WebDriverWait(driver, 15).until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, "//a[@href='/']")),
                    EC.presence_of_element_located((By.XPATH, "//a[@href='/explore/']")),
                    EC.presence_of_element_located((By.XPATH, "//a[@href='/reels/']")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(@aria-label, 'Profile')]")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Log Out')]"))
                )
            )
            logging.info(f"Successfully logged in to Instagram for {username}")
        except Exception as e:
            raise Exception(f"Login verification failed: {e}")

        # Extract and save cookies
        cookies = driver.get_cookies()
        if not cookies:
            raise Exception("No cookies found after login")
        
        session = {cookie["name"]: cookie["value"] for cookie in cookies}
        
        # Save session to file
        with open(session_file, "w", encoding='utf-8') as f:
            json.dump(session, f, indent=2)
        logging.info(f"Session saved to {session_file}")
        return session

    except Exception as e:
        logging.error(f"Selenium login failed for {username}: {e}")
        raise
    finally:
        time.sleep(2)
        driver.quit()

class InstaDM:
    def __init__(self, username, password, session_file=None, use_browser=False):
        self.client = Client()
        self.username = username
        self.password = password
        self.session_file = session_file or f"session_{username}.json"
        self.use_browser = use_browser  # New option for browser-based DM sending
        self.driver = None  # Selenium driver for browser mode
        self.sent_dms = {}  # Track sent DMs: {username: (user_id, thread_id)}
        self.replied_messages = set()  # Track replied message IDs
        self.replied_messages_file = f"{username}_replied_messages.json"
        self._load_replied_messages()
        self._login()

    def _load_replied_messages(self):
        """Load replied message IDs from JSON file."""
        try:
            if os.path.exists(self.replied_messages_file):
                with open(self.replied_messages_file, 'r', encoding='utf-8') as f:
                    self.replied_messages = set(json.load(f))
                logging.info(f"Loaded {len(self.replied_messages)} replied message IDs from {self.replied_messages_file}")
        except Exception as e:
            logging.error(f"Error loading replied messages: {e}")

    def _save_replied_messages(self):
        """Save replied message IDs to JSON file."""
        try:
            with open(self.replied_messages_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.replied_messages), f)
            logging.info(f"Saved replied message IDs to {self.replied_messages_file}")
        except Exception as e:
            logging.error(f"Error saving replied messages: {e}")

    def _login(self):
        # Try to load existing session from DB first
        session_data = db.get_session(self.username)
        if session_data:
            try:
                self.client.load_settings(session_data)
                self.client.login(self.username, self.password)
                logging.info(f"✅ Loaded existing session for {self.username} from DB - using instagrapi")
                return
            except Exception as e:
                logging.warning(f"Failed to load session from DB for {self.username}: {e}")
                logging.info(f"Will create new session using browser login...")
        
        if self.use_browser:
            # Use browser login to create session, then transfer to instagrapi
            self._browser_login_and_transfer()
        else:
            # Fallback to direct API login
            self.client.login(self.username, self.password)
            # Save session to DB
            db.save_session(self.username, self.client.get_settings())
            logging.info(f"Saved session for {self.username} to DB.")
    
    def _browser_login_and_transfer(self):
        """Login via browser (visible), extract session, transfer to instagrapi for DM sending"""
        try:
            logging.info(f"🌐 Starting BROWSER LOGIN for {self.username} - You will see the browser!")
            
            # Initialize browser (visible mode)
            options = Options()
            # HEAD MODE - Remove headless arguments to show browser
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            # Optional: Set window size for better visibility
            options.add_argument("--window-size=1200,800")
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Navigate to Instagram
            driver.get("https://www.instagram.com")
            time.sleep(random.uniform(3, 6))
            
            # Fill login form
            username_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = driver.find_element(By.NAME, "password")
            
            # Type credentials with human-like delays
            logging.info(f"🔑 Typing username: {self.username}")
            for char in self.username:
                username_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(random.uniform(0.5, 1.5))
            
            logging.info(f"🔐 Typing password...")
            for char in self.password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(random.uniform(0.5, 1.5))
            
            # Click login button
            logging.info(f"🚀 Clicking login button...")
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(8)
            
            # Check for verification requests (Gmail code, phone code, etc.)
            logging.info(f"🔍 Checking for verification requests...")
            
            # Wait up to 80 seconds for user to complete verification
            verification_wait_time = 80  # 80 seconds
            start_time = time.time()
            
            while time.time() - start_time < verification_wait_time:
                try:
                    # Check if we're on the main Instagram page (login successful)
                    WebDriverWait(driver, 5).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.XPATH, "//a[@href='/']")),
                            EC.presence_of_element_located((By.XPATH, "//a[@href='/explore/']")),
                            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Home')]")),
                        )
                    )
                    logging.info(f"✅ Browser login successful for {self.username}")
                    break
                    
                except:
                    # Check for verification elements
                    try:
                        # Look for verification code input fields
                        verification_elements = driver.find_elements(By.XPATH, 
                            "//input[@placeholder='Confirmation code'] | //input[@placeholder='Security code'] | //input[@placeholder='Verification code']")
                        
                        if verification_elements:
                            remaining_time = int(verification_wait_time - (time.time() - start_time))
                            logging.info(f"📱 Verification required! Please enter the code. Browser will wait {remaining_time} seconds...")
                            
                            # Wait 10 seconds before checking again
                            time.sleep(10)
                            continue
                            
                    except:
                        pass
                    
                    # Check for other verification pages
                    try:
                        if "challenge" in driver.current_url.lower() or "verify" in driver.current_url.lower():
                            remaining_time = int(verification_wait_time - (time.time() - start_time))
                            logging.info(f"🔐 Instagram verification page detected. Please complete verification. Browser will wait {remaining_time} seconds...")
                            time.sleep(10)
                            continue
                    except:
                        pass
                    
                    # Wait a bit before checking again
                    time.sleep(5)
            
            # If we timed out, check one more time
            if time.time() - start_time >= verification_wait_time:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.XPATH, "//a[@href='/']")),
                            EC.presence_of_element_located((By.XPATH, "//a[@href='/explore/']")),
                            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Home')]")),
                        )
                    )
                    logging.info(f"✅ Browser login successful for {self.username} after verification")
                except Exception as e:
                    logging.warning(f"⚠️ Verification timeout reached. Proceeding with current state...")
            
            # Handle potential popups after successful login
            try:
                not_now_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                )
                not_now_button.click()
                logging.info(f"📱 Dismissed 'Save Login Info' popup")
                time.sleep(2)
            except:
                pass
            
            try:
                not_now_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not now')]"))
                )
                not_now_button.click()
                logging.info(f"🔔 Dismissed notifications popup")
                time.sleep(2)
            except:
                pass
            
            # Extract cookies and convert to instagrapi session
            logging.info(f"🍪 Extracting session cookies...")
            cookies = driver.get_cookies()
            if not cookies:
                raise Exception("No cookies found after login")
            
            # Convert cookies to instagrapi format
            session_data = {}
            for cookie in cookies:
                session_data[cookie["name"]] = cookie["value"]
            
            # Close browser - we're done with the visual part
            driver.quit()
            logging.info(f"🌐 Browser closed - switching to API mode for DM sending")
            
            # Transfer session to instagrapi
            self._transfer_session_to_instagrapi(session_data)
            
        except Exception as e:
            logging.error(f"Browser login failed for {self.username}: {e}")
            if 'driver' in locals():
                driver.quit()
            # Fallback to direct API login
            logging.info(f"⚡ Falling back to direct API login...")
            self.client.login(self.username, self.password)
            db.save_session(self.username, self.client.get_settings())
    
    def _transfer_session_to_instagrapi(self, browser_session_data):
        """Transfer browser session to instagrapi client"""
        try:
            logging.info(f"🔄 Transferring browser session to instagrapi...")
            
            # Method 1: Try to use browser cookies with instagrapi
            # Extract key cookies needed for Instagram API
            required_cookies = ['sessionid', 'ds_user_id', 'csrftoken']
            instagrapi_session = {}
            
            for cookie_name in required_cookies:
                if cookie_name in browser_session_data:
                    instagrapi_session[cookie_name] = browser_session_data[cookie_name]
            
            if len(instagrapi_session) >= 2:  # At least sessionid and ds_user_id
                # Try to create instagrapi session from browser cookies
                try:
                    # Set cookies in instagrapi client
                    for name, value in instagrapi_session.items():
                        self.client.set_cookie(name, value)
                    
                    # Test the session by getting account info
                    account_info = self.client.account_info()
                    logging.info(f"✅ Successfully transferred browser session to instagrapi!")
                    logging.info(f"👤 Account info: @{account_info.username} (ID: {account_info.pk})")
                    
                    # Save the working session
                    db.save_session(self.username, self.client.get_settings())
                    return
                    
                except Exception as e:
                    logging.warning(f"Failed to use browser cookies directly: {e}")
            
            # Method 2: Fallback - fresh instagrapi login (but with warm session from browser)
            logging.info(f"🔥 Browser warmed up the account - now doing fresh instagrapi login...")
            self.client.login(self.username, self.password)
            
            # Save session to DB
            db.save_session(self.username, self.client.get_settings())
            logging.info(f"✅ Fresh instagrapi login successful - session saved!")
            
        except Exception as e:
            logging.error(f"Failed to transfer session: {e}")
            # Last resort - direct login
            self.client.login(self.username, self.password)
            db.save_session(self.username, self.client.get_settings())

    def send_dm(self, userdm, messageText, engagement_settings=None):
        # Always use API for DM sending (fast and reliable)
        # Browser is only used for initial login and session creation
        result = self._send_dm_api(userdm, messageText)
        
        # If DM was successful and auto_engage is enabled, perform engagement actions
        if result[0] and engagement_settings and engagement_settings.get('auto_engage', False):
            self._auto_engage_user(userdm, engagement_settings)
        
        return result
    
    def _send_dm_api(self, userdm, messageText):
        """Send DM via API (instagrapi) - invisible method with multiple fallback strategies"""
        try:
            # METHOD 1: Try direct API call with manual user ID extraction
            user_id = None
            
            # Try multiple ways to get user ID
            for attempt in range(3):
                try:
                    if attempt == 0:
                        # Method 1: Standard way
                        user_id = self.client.user_id_from_username(userdm)
                    elif attempt == 1:
                        # Method 2: Search by username
                        logging.info(f"Trying search method for {userdm}...")
                        users = self.client.search_users(userdm, count=1)
                        if users:
                            user_id = users[0].pk
                    elif attempt == 2:
                        # Method 3: Manual API call
                        logging.info(f"Trying manual API method for {userdm}...")
                        user_id = self._get_user_id_manual(userdm)
                    
                    if user_id:
                        logging.info(f"Found user ID for {userdm}: {user_id}")
                        break
                        
                except Exception as e:
                    logging.warning(f"Method {attempt + 1} failed for {userdm}: {str(e)[:100]}")
                    continue
            
            if not user_id:
                raise Exception(f"Could not find user ID for {userdm} after trying all methods")
            
            # Try to send DM with multiple methods
            success = False
            thread_id = "unknown"
            
            for dm_attempt in range(2):
                try:
                    time.sleep(random.uniform(1, 3))  # Rate limiting
                    
                    if dm_attempt == 0:
                        # Method 1: Standard direct_send
                        logging.info(f"Attempting standard DM send to {userdm}...")
                        direct_message = self.client.direct_send(messageText, [int(user_id)])
                        
                        # Extract thread_id
                        if hasattr(direct_message, 'thread_id'):
                            thread_id = str(direct_message.thread_id)
                        elif hasattr(direct_message, 'id'):
                            thread_id = str(direct_message.id)
                        else:
                            thread_id = "dm_sent"
                        
                        success = True
                        break
                        
                    elif dm_attempt == 1:
                        # Method 2: Try with thread
                        logging.info(f"Attempting thread-based DM send to {userdm}...")
                        thread = self.client.direct_thread_by_participants([int(user_id)])
                        if thread:
                            self.client.direct_send_item("text", messageText, thread_ids=[thread.id])
                            thread_id = str(thread.id)
                            success = True
                            break
                        
                except Exception as dm_error:
                    error_str = str(dm_error).lower()
                    if "validation" in error_str or "pydantic" in error_str:
                        # Validation errors often mean the message was sent
                        logging.warning(f"Validation error on attempt {dm_attempt + 1} for {userdm} - assuming success")
                        success = True
                        thread_id = "validation_success"
                        break
                    else:
                        logging.warning(f"DM attempt {dm_attempt + 1} failed for {userdm}: {str(dm_error)[:100]}")
                        continue
            
            if success:
                db.track_dm_sent(self.username, userdm, messageText, thread_id=thread_id)
                logging.info(f"✅ Successfully sent DM to {userdm}")
                return True, None
            else:
                raise Exception("All DM sending methods failed")
                
        except Exception as e:
            error_msg = str(e)
            # Even on "failure", validation errors usually mean success
            if "validation" in error_msg.lower() or "pydantic" in error_msg.lower():
                logging.warning(f"⚠️ Validation error for {userdm} - treating as success: {error_msg[:100]}...")
                db.track_dm_sent(self.username, userdm, messageText, thread_id="validation_assumed_success")
                return True, None
            else:
                logging.error(f"❌ All methods failed for {userdm}: {error_msg}")
                db.track_dm_failed(self.username, userdm, str(e))
                return False, str(e)
    
    def _get_user_id_manual(self, username):
        """Manual method to get user ID bypassing validation"""
        try:
            # Try to extract user ID from Instagram's web API
            import requests
            
            # Use the same session as instagrapi
            response = self.client.private_request(f"users/{username}/usernameinfo/")
            
            if response and "user" in response:
                user_data = response["user"]
                if "pk" in user_data:
                    return str(user_data["pk"])
                elif "id" in user_data:
                    return str(user_data["id"])
            
            return None
            
        except Exception as e:
            logging.warning(f"Manual user ID extraction failed: {e}")
            return None
    


    def check_and_reply_dms(self, target_username=None):
        """
        Enhanced DM checking and auto-reply functionality
        """
        try:
            # Keyword responses with engaging replies
            keyword_responses = {
                r"\b(hey|hi|hello)\b": lambda user: f"Yo {user}! Stoked you replied! What's the deal? 😎",
                r"\bhow are you\b": lambda user: f"Hey {user}! I'm pumped—how's your day going? 😄",
                r"\b(interested|intereted|great|cool|awesome)\b": lambda user: f"Wow, {user}, that's lit! Can you spill more details? 👀",
                r"\b(yes|sure|okay)\b": lambda user: f"Sweet, {user}! Let's roll—what's next on your mind? 🚀",
                r"\b(no|not really)\b": lambda user: f"No worries, {user}! Anything else I can hook you up with? 😊",
            }

            # Fetch latest threads
            threads = self._get_threads()
            if not threads:
                return False, "Failed to retrieve threads"

            replied = False
            target_user_id = None
            target_thread_id = None
            
            if target_username and target_username in self.sent_dms:
                target_user_id, target_thread_id = self.sent_dms[target_username]

            # Process messages from threads
            for thread in threads:
                if replied:
                    break
                    
                thread_id = self._extract_thread_id(thread)
                if not thread_id:
                    continue
                
                messages = self._extract_messages(thread)
                if not messages:
                    continue
                
                # Process messages in this thread
                for message in messages:
                    if replied:
                        break
                        
                    message_id = self._extract_message_id(message)
                    if not message_id or message_id in self.replied_messages:
                        continue
                    
                    user_id = self._extract_user_id(message)
                    text = self._extract_message_text(message)
                    
                    if not user_id or not text:
                        continue
                    
                    # Check if this is a reply to our message
                    if target_thread_id and thread_id == target_thread_id:
                        # This is a reply in our target thread
                        replied = self._process_reply(user_id, text, message_id, keyword_responses)
                    else:
                        # Check if this is a general reply
                        replied = self._process_reply(user_id, text, message_id, keyword_responses)

            # Save replied messages
            self._save_replied_messages()
            
            return replied, None
            
        except Exception as e:
            logging.error(f"Error in check_and_reply_dms: {e}")
            return False, str(e)
    
    def like_post(self, post_url_or_code):
        """Like a post by URL or media code"""
        try:
            # Extract media code from URL if provided
            if "instagram.com" in post_url_or_code:
                # Extract code from URL patterns like /p/CODE/ or /reel/CODE/
                match = re.search(r'/(p|reel)/([A-Za-z0-9_-]+)/', post_url_or_code)
                if match:
                    media_code = match.group(2)
                else:
                    raise ValueError("Invalid Instagram post URL")
            else:
                media_code = post_url_or_code
            
            # Get media ID from code
            media_id = self.client.media_pk_from_code(media_code)
            
            # Like the post
            result = self.client.media_like(media_id)
            
            if result:
                logging.info(f"{color.GREEN}✓ Successfully liked post: {media_code}{color.RESET_ALL}")
                db.track_engagement(self.username, "like", media_code, "success")
                return True, None
            else:
                raise Exception("Like operation returned False")
                
        except Exception as e:
            error_msg = str(e)
            logging.error(f"{color.RED}✗ Failed to like post {post_url_or_code}: {error_msg}{color.RESET_ALL}")
            db.track_engagement(self.username, "like", post_url_or_code, "failed", error_msg)
            return False, error_msg
    
    def comment_post(self, post_url_or_code, comment_text):
        """Comment on a post by URL or media code"""
        try:
            # Extract media code from URL if provided
            if "instagram.com" in post_url_or_code:
                match = re.search(r'/(p|reel)/([A-Za-z0-9_-]+)/', post_url_or_code)
                if match:
                    media_code = match.group(2)
                else:
                    raise ValueError("Invalid Instagram post URL")
            else:
                media_code = post_url_or_code
            
            # Get media ID from code
            media_id = self.client.media_pk_from_code(media_code)
            
            # Add the comment
            comment = self.client.media_comment(media_id, comment_text)
            
            if comment:
                logging.info(f"{color.GREEN}✓ Successfully commented on post {media_code}: {comment_text}{color.RESET_ALL}")
                db.track_engagement(self.username, "comment", media_code, "success", comment_text)
                return True, None
            else:
                raise Exception("Comment operation returned None")
                
        except Exception as e:
            error_msg = str(e)
            logging.error(f"{color.RED}✗ Failed to comment on post {post_url_or_code}: {error_msg}{color.RESET_ALL}")
            db.track_engagement(self.username, "comment", post_url_or_code, "failed", error_msg)
            return False, error_msg
    
    def watch_story(self, username_or_url):
        """Watch a user's story by username or story URL"""
        try:
            # Extract username from URL if provided
            if "instagram.com" in username_or_url:
                # Handle story URLs like /stories/username/
                match = re.search(r'/stories/([A-Za-z0-9_.]+)/', username_or_url)
                if match:
                    target_username = match.group(1)
                else:
                    # Try to extract from profile URL
                    match = re.search(r'instagram.com/([A-Za-z0-9_.]+)', username_or_url)
                    if match:
                        target_username = match.group(1).rstrip('/')
                    else:
                        raise ValueError("Invalid Instagram URL")
            else:
                target_username = username_or_url
            
            # Get user ID
            user_id = self.client.user_id_from_username(target_username)
            
            # Get user's stories
            stories = self.client.user_stories(user_id)
            
            if not stories:
                logging.info(f"{color.YELLOW}No active stories found for {target_username}{color.RESET_ALL}")
                return False, "No active stories"
            
            # Watch each story
            watched_count = 0
            for story in stories:
                try:
                    # Mark story as seen
                    self.client.story_seen([story.id])
                    watched_count += 1
                    logging.info(f"{color.GREEN}✓ Watched story {watched_count}/{len(stories)} from {target_username}{color.RESET_ALL}")
                    time.sleep(random.uniform(2, 5))  # Simulate watching time
                except Exception as story_error:
                    logging.warning(f"Failed to watch story {story.id}: {story_error}")
            
            if watched_count > 0:
                logging.info(f"{color.GREEN}✓ Successfully watched {watched_count} stories from {target_username}{color.RESET_ALL}")
                db.track_engagement(self.username, "story_view", target_username, "success", f"Watched {watched_count} stories")
                return True, f"Watched {watched_count} stories"
            else:
                raise Exception("Failed to watch any stories")
                
        except Exception as e:
            error_msg = str(e)
            logging.error(f"{color.RED}✗ Failed to watch stories from {username_or_url}: {error_msg}{color.RESET_ALL}")
            db.track_engagement(self.username, "story_view", username_or_url, "failed", error_msg)
            return False, error_msg
    
    def follow_user(self, username_or_url):
        """Follow a user by username or profile URL"""
        try:
            # Extract username from URL if provided
            if "instagram.com" in username_or_url:
                match = re.search(r'instagram.com/([A-Za-z0-9_.]+)', username_or_url)
                if match:
                    target_username = match.group(1).rstrip('/')
                else:
                    raise ValueError("Invalid Instagram profile URL")
            else:
                target_username = username_or_url
            
            # Get user ID
            user_id = self.client.user_id_from_username(target_username)
            
            # Follow the user
            result = self.client.user_follow(user_id)
            
            if result:
                logging.info(f"{color.GREEN}✓ Successfully followed {target_username}{color.RESET_ALL}")
                db.track_engagement(self.username, "follow", target_username, "success")
                return True, None
            else:
                raise Exception("Follow operation returned False")
                
        except Exception as e:
            error_msg = str(e)
            logging.error(f"{color.RED}✗ Failed to follow {username_or_url}: {error_msg}{color.RESET_ALL}")
            db.track_engagement(self.username, "follow", username_or_url, "failed", error_msg)
            return False, error_msg
    
    def get_engagement_stats(self):
        """Get engagement statistics for this account"""
        try:
            stats = db.get_engagement_stats(self.username)
            return stats
        except Exception as e:
            logging.error(f"Failed to get engagement stats: {e}")
            return None
    
    def _auto_engage_user(self, target_username, settings):
        """Automatically engage with user after sending DM based on settings"""
        try:
            logging.info(f"{color.BLUE}Starting auto-engagement for {target_username}{color.RESET_ALL}")
            
            # Get user ID
            user_id = self.client.user_id_from_username(target_username)
            
            # 1. Watch their stories (if enabled)
            if settings.get('auto_story', False):
                try:
                    stories = self.client.user_stories(user_id)
                    if stories:
                        for story in stories[:3]:  # Watch up to 3 stories
                            self.client.story_seen([story.id])
                            time.sleep(random.uniform(2, 4))
                        logging.info(f"{color.GREEN}✓ Watched {len(stories[:3])} stories from {target_username}{color.RESET_ALL}")
                        db.track_engagement(self.username, "story_view", target_username, "success", f"Auto-engaged after DM")
                except Exception as e:
                    logging.warning(f"Could not watch stories for {target_username}: {e}")
            
            # 2. Like their recent posts (if enabled)
            if settings.get('auto_like', False):
                try:
                    # Get user's recent posts
                    medias = self.client.user_medias(user_id, amount=3)  # Get last 3 posts
                    liked_count = 0
                    
                    for media in medias:
                        try:
                            # Like the post
                            self.client.media_like(media.id)
                            liked_count += 1
                            logging.info(f"{color.GREEN}✓ Liked post from {target_username}{color.RESET_ALL}")
                            db.track_engagement(self.username, "like", str(media.code), "success", "Auto-engaged after DM")
                            time.sleep(random.uniform(3, 6))  # Wait between likes
                        except Exception as e:
                            logging.warning(f"Could not like post {media.code}: {e}")
                    
                    if liked_count > 0:
                        logging.info(f"{color.GREEN}✓ Liked {liked_count} posts from {target_username}{color.RESET_ALL}")
                except Exception as e:
                    logging.warning(f"Could not like posts for {target_username}: {e}")
            
            # 3. Follow the user (if enabled)
            if settings.get('auto_follow', False):
                try:
                    self.client.user_follow(user_id)
                    logging.info(f"{color.GREEN}✓ Followed {target_username}{color.RESET_ALL}")
                    db.track_engagement(self.username, "follow", target_username, "success", "Auto-engaged after DM")
                    time.sleep(random.uniform(2, 4))
                except Exception as e:
                    logging.warning(f"Could not follow {target_username}: {e}")
            
            # 4. Comment on a post (if enabled)
            if settings.get('auto_comment', False):
                try:
                    medias = self.client.user_medias(user_id, amount=1)
                    if medias:
                        comments = ["Great post! 🔥", "Love this! 💯", "Amazing content! 👏", "This is awesome! 🙌", "So cool! 😍", "Nice! 👍", "Wow! 🤩", "Beautiful! ❤️"]
                        comment_text = random.choice(comments)
                        self.client.media_comment(medias[0].id, comment_text)
                        logging.info(f"{color.GREEN}✓ Commented on post from {target_username}: {comment_text}{color.RESET_ALL}")
                        db.track_engagement(self.username, "comment", str(medias[0].code), "success", comment_text)
                except Exception as e:
                    logging.warning(f"Could not comment on post for {target_username}: {e}")
            
            logging.info(f"{color.BLUE}Completed auto-engagement for {target_username}{color.RESET_ALL}")
            
        except Exception as e:
            logging.error(f"Error in auto-engagement for {target_username}: {e}")

    def logout(self):
        """Clean up resources and logout"""
        try:
            # No browser driver to close in hybrid mode (already closed after login)
            if hasattr(self, 'client'):
                # No explicit logout needed for instagrapi
                pass
            logging.info(f"Logged out {self.username}")
        except Exception as e:
            logging.error(f"Error during logout for {self.username}: {e}")

    def _get_threads(self):
        """Get threads with retry logic"""
        for attempt in range(3):
            try:
                threads_response = self.client.direct_threads(amount=10)
                
                if threads_response is None:
                    logging.warning("No threads returned")
                    time.sleep(random.uniform(2, 5))
                    continue
                
                if isinstance(threads_response, list):
                    return threads_response
                elif hasattr(threads_response, 'data') and isinstance(threads_response.data, list):
                    return threads_response.data
                elif hasattr(threads_response, 'threads') and isinstance(threads_response.threads, list):
                    return threads_response.threads
                elif isinstance(threads_response, dict) and 'threads' in threads_response:
                    return threads_response['threads']
                else:
                    logging.warning(f"Unknown thread response format: {type(threads_response)}")
                    time.sleep(random.uniform(2, 5))
                    continue
                    
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed to fetch DMs: {e}")
                time.sleep(random.uniform(3, 7))
        
        return []

    def _extract_thread_id(self, thread):
        """Extract thread ID from thread object"""
        if hasattr(thread, 'id'):
            return thread.id
        elif isinstance(thread, dict) and 'thread_id' in thread:
            return thread['thread_id']
        elif isinstance(thread, dict) and 'id' in thread:
            return thread['id']
        return None

    def _extract_messages(self, thread):
        """Extract messages from thread object"""
        if hasattr(thread, 'messages') and thread.messages:
            return thread.messages or []
        elif isinstance(thread, dict) and 'messages' in thread and thread['messages']:
            return thread['messages']
        elif isinstance(thread, dict) and 'items' in thread and thread['items']:
            return thread['items']
        return []

    def _extract_message_id(self, message):
        """Extract message ID from message object"""
        if hasattr(message, 'id'):
            return message.id
        elif isinstance(message, dict) and 'id' in message:
            return message['id']
        return None

    def _extract_user_id(self, message):
        """Extract user ID from message object"""
        if hasattr(message, 'user_id'):
            return message.user_id
        elif isinstance(message, dict) and 'user_id' in message:
            return message['user_id']
        return None

    def _extract_message_text(self, message):
        """Extract message text from message object"""
        if hasattr(message, 'text') and message.text:
            return message.text
        elif isinstance(message, dict) and 'text' in message and message['text']:
            return message['text']
        return ""

    def _process_reply(self, user_id, text, message_id, keyword_responses):
        """Process a reply and send auto-response if appropriate"""
        try:
            # Get username from user_id
            user_info = self.client.user_info(user_id)
            username = user_info.username
            
            # Check for keyword matches
            for pattern, response_func in keyword_responses.items():
                if re.search(pattern, text, re.IGNORECASE):
                    reply_text = response_func(username)
                    
                    # Send reply
                    success, error = self.send_dm(username, reply_text)
                    if success:
                        self.replied_messages.add(message_id)
                        logging.info(f"{color.GREEN}Auto-replied to {username}: {reply_text}{color.RESET_ALL}")
                        return True
                    else:
                        logging.error(f"Failed to send auto-reply to {username}: {error}")
            
            return False
            
        except Exception as e:
            logging.error(f"Error processing reply: {e}")
            return False

    def logout(self):
        """Logout and cleanup"""
        try:
            self.client.logout()
            logging.info(f"Logged out from {self.username}")
        except Exception as e:
            logging.error(f"Error during logout for {self.username}: {e}")

def main():
    """Main function for testing"""
    # Example usage
    username = "your_username"
    password = "your_password"
    session_file = f"session_{username}.json"
    
    try:
        insta = InstaDM(username, password, session_file)
        print("Login successful!")
        
        # Test sending a DM
        success, error = insta.send_dm("target_username", "Hello! This is a test message.")
        if success:
            print("DM sent successfully!")
        else:
            print(f"Failed to send DM: {error}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'insta' in locals():
            insta.logout()

if __name__ == "__main__":
    main()