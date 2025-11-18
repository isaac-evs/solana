"""
Configuration module for IPFS + Solana application
"""
import os
from pathlib import Path

# Solana Configuration
SOLANA_RPC = "https://api.devnet.solana.com"
SOLANA_NETWORK = "devnet"

# IPFS Configuration
IPFS_API_ADDR = "/ip4/127.0.0.1/tcp/5001"
IPFS_GATEWAY = "http://localhost:8080/ipfs/"
IPFS_TIMEOUT = 30

# Application Configuration
APP_NAME = "IPFS Solana Manager"
APP_VERSION = "2.0.0"

# Security Configuration
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_FILE_EXTENSIONS = ['.pdf', '.txt', '.json', '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mp3']

# Paths Configuration
def get_home_dir() -> Path:
    """Get user home directory in a cross-platform way"""
    return Path.home()

def get_default_save_dir() -> Path:
    """Get default save directory (Desktop or Home)"""
    desktop = get_home_dir() / "Desktop"
    return desktop if desktop.exists() else get_home_dir()

def get_data_dir() -> Path:
    """Get application data directory"""
    data_dir = get_home_dir() / ".ipfs-solana-manager"
    data_dir.mkdir(exist_ok=True)
    return data_dir

def get_logs_dir() -> Path:
    """Get logs directory"""
    logs_dir = get_data_dir() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir
