"""
Authentication Service - Simple login functionality
"""
import hashlib
import secrets
import bcrypt
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
from backend.config import get_data_dir
from backend.utils.logger import setup_logger

logger = setup_logger("auth_service")

# Word lists for generating readable usernames
ADJECTIVES = [
    "happy", "sad", "brave", "shy", "calm", "wild", "swift", "gentle", 
    "fierce", "clever", "wise", "silly", "proud", "humble", "bold", "quiet",
    "bright", "dark", "cool", "warm", "smooth", "rough", "sweet", "spicy"
]

ANIMALS = [
    "gorilla", "panda", "tiger", "lion", "eagle", "hawk", "wolf", "bear",
    "fox", "deer", "owl", "raven", "dolphin", "whale", "shark", "otter",
    "koala", "lemur", "lynx", "badger", "falcon", "moose", "bison", "cobra",
    "penguin", "seal", "walrus", "turtle", "gecko", "iguana", "falcon", "crane"
]

class AuthService:
    """Service class for authentication"""
    
    def __init__(self):
        self.sessions = {}  # In-memory session storage
        self.session_timeout = timedelta(hours=24)  # 24 hour sessions
        self.failed_attempts = {}  # Track failed login attempts
        self.lockout_duration = timedelta(minutes=15)  # Lockout for 15 minutes
        self.max_attempts = 5  # Max failed attempts before lockout
        self._load_users()
    
    def _load_users(self):
        """Load users from file or create default user"""
        self.users_file = get_data_dir() / "users.txt"
        self.users = {}
        
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and ':' in line:
                            username, password_hash = line.split(':', 1)
                            # Check if it's an old SHA-256 hash (64 hex chars)
                            # vs new bcrypt hash (starts with $2b$)
                            if len(password_hash) == 64 and not password_hash.startswith('$'):
                                logger.warning(f"User {username} has old SHA-256 hash, will be migrated on next login")
                            self.users[username] = password_hash
                logger.info(f"Loaded {len(self.users)} users")
            except Exception as e:
                logger.error(f"Failed to load users: {str(e)}")
        
        # Create default user if no users exist
        if not self.users:
            self._create_default_user()
    
    def _create_default_user(self):
        """Create default user with random secure credentials"""
        # Generate readable username (e.g., "swiftpanda", "bravewolf")
        username = self._generate_username()
        
        # Generate strong random password (16-24 characters)
        password = self._generate_password()
        
        password_hash = self._hash_password(password)
        self.users[username] = password_hash
        self._save_users()
        
        # Save credentials to a welcome file
        self._save_welcome_credentials(username, password)
        
        logger.info(f"Created secure user with random credentials - Username: {username}")
    
    def _generate_username(self) -> str:
        """Generate a readable username like Reddit (e.g., 'swiftpanda')"""
        adjective = random.choice(ADJECTIVES)
        animal = random.choice(ANIMALS)
        # Add random number for uniqueness (2-3 digits)
        number = random.randint(10, 999)
        return f"{adjective}{animal}{number}"
    
    def _generate_password(self) -> str:
        """Generate a strong random password (20 characters)"""
        # Use URL-safe base64 which gives us readable characters
        # 20 characters provides ~120 bits of entropy
        return secrets.token_urlsafe(15)  # This gives us ~20 chars
    
    def _save_welcome_credentials(self, username: str, password: str):
        """Save credentials to a welcome file that user must read"""
        welcome_file = get_data_dir() / "WELCOME_CREDENTIALS.txt"
        
        try:
            with open(welcome_file, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write("  IPFS SOLANA MANAGER - SECURE LOGIN CREDENTIALS\n")
                f.write("=" * 70 + "\n\n")
                f.write("⚠️  IMPORTANT: SAVE THESE CREDENTIALS NOW! ⚠️\n\n")
                f.write("These credentials are randomly generated for maximum security.\n")
                f.write("They will NOT be shown again. If you lose them, you'll need to\n")
                f.write("delete the users.txt file and restart the application.\n\n")
                f.write("-" * 70 + "\n")
                f.write(f"USERNAME: {username}\n")
                f.write(f"PASSWORD: {password}\n")
                f.write("-" * 70 + "\n\n")
                f.write("📝 Write these down or save them in a password manager NOW!\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 70 + "\n")
            
            logger.info(f"Welcome credentials saved to: {welcome_file}")
            
        except Exception as e:
            logger.error(f"Failed to save welcome credentials: {str(e)}")
    
    def _save_users(self):
        """Save users to file"""
        try:
            self.users_file.parent.mkdir(exist_ok=True)
            with open(self.users_file, 'w', encoding='utf-8') as f:
                for username, password_hash in self.users.items():
                    f.write(f"{username}:{password_hash}\n")
            logger.info("Users saved successfully")
        except Exception as e:
            logger.error(f"Failed to save users: {str(e)}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt (secure with salt)"""
        # bcrypt automatically handles salting
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against bcrypt hash (with legacy SHA-256 support)"""
        try:
            # Check if it's an old SHA-256 hash (64 hex characters)
            if len(password_hash) == 64 and not password_hash.startswith('$'):
                # Legacy SHA-256 verification
                old_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
                return old_hash == password_hash
            
            # Modern bcrypt verification
            password_bytes = password.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user and create session
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Dictionary containing session token and user info
            
        Raises:
            Exception: If authentication fails
        """
        try:
            # Check if user is locked out
            if username in self.failed_attempts:
                lockout_info = self.failed_attempts[username]
                if lockout_info['count'] >= self.max_attempts:
                    lockout_until = lockout_info['locked_at'] + self.lockout_duration
                    if datetime.now() < lockout_until:
                        remaining = (lockout_until - datetime.now()).seconds // 60
                        raise Exception(f"Account locked. Try again in {remaining} minutes")
                    else:
                        # Lockout expired, reset counter
                        del self.failed_attempts[username]
            
            # Validate credentials
            if username not in self.users:
                self._record_failed_attempt(username)
                raise Exception("Invalid username or password")
            
            if not self._verify_password(password, self.users[username]):
                self._record_failed_attempt(username)
                raise Exception("Invalid username or password")
            
            # Migrate old SHA-256 hash to bcrypt on successful login
            current_hash = self.users[username]
            if len(current_hash) == 64 and not current_hash.startswith('$'):
                logger.info(f"Migrating user {username} from SHA-256 to bcrypt")
                new_hash = self._hash_password(password)
                self.users[username] = new_hash
                self._save_users()
            
            # Clear failed attempts on successful login
            if username in self.failed_attempts:
                del self.failed_attempts[username]
            
            # Create session
            session_token = secrets.token_urlsafe(32)
            session_data = {
                "username": username,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + self.session_timeout
            }
            
            self.sessions[session_token] = session_data
            
            logger.info(f"User logged in: {username}")
            
            return {
                "success": True,
                "token": session_token,
                "username": username,
                "expires_at": session_data["expires_at"].isoformat()
            }
        
        except Exception as e:
            logger.warning(f"Login failed for user {username}: {str(e)}")
            raise Exception(str(e))
    
    def _record_failed_attempt(self, username: str):
        """Record a failed login attempt"""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = {
                'count': 1,
                'locked_at': datetime.now()
            }
        else:
            self.failed_attempts[username]['count'] += 1
            if self.failed_attempts[username]['count'] >= self.max_attempts:
                self.failed_attempts[username]['locked_at'] = datetime.now()
                logger.warning(f"Account locked due to multiple failed attempts: {username}")
    
    def logout(self, token: str) -> Dict[str, Any]:
        """
        Logout user and destroy session
        
        Args:
            token: Session token
            
        Returns:
            Dictionary containing logout status
        """
        if token in self.sessions:
            username = self.sessions[token]["username"]
            del self.sessions[token]
            logger.info(f"User logged out: {username}")
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
    
    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate session token
        
        Args:
            token: Session token
            
        Returns:
            Session data if valid, None otherwise
        """
        if token not in self.sessions:
            return None
        
        session_data = self.sessions[token]
        
        # Check if session expired
        if datetime.now() > session_data["expires_at"]:
            del self.sessions[token]
            logger.info(f"Session expired for user: {session_data['username']}")
            return None
        
        return session_data
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change user password
        
        Args:
            username: Username
            old_password: Current password
            new_password: New password
            
        Returns:
            Dictionary containing change status
            
        Raises:
            Exception: If password change fails
        """
        try:
            # Validate old password
            if username not in self.users:
                raise Exception("User not found")
            
            if not self._verify_password(old_password, self.users[username]):
                raise Exception("Current password is incorrect")
            
            # Validate new password
            if len(new_password) < 6:
                raise Exception("New password must be at least 6 characters")
            
            # Update password
            new_password_hash = self._hash_password(new_password)
            self.users[username] = new_password_hash
            self._save_users()
            
            logger.info(f"Password changed for user: {username}")
            
            return {
                "success": True,
                "message": "Password changed successfully"
            }
        
        except Exception as e:
            logger.warning(f"Password change failed for user {username}: {str(e)}")
            raise Exception(str(e))
