"""
API Server - Flask backend for Tauri frontend
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from pathlib import Path
from functools import wraps
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import APP_NAME, APP_VERSION, get_default_save_dir, get_data_dir
from backend.services.ipfs_service import IPFSService
from backend.services.solana_service import SolanaService
from backend.services.auth_service import AuthService
from backend.utils.logger import setup_logger
from backend.utils.security import ValidationError

# Initialize Flask app
app = Flask(__name__)

# Configure CORS - only allow localhost and Tauri origins
# Tauri uses tauri://localhost and http://localhost:3000 in dev mode
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "tauri://localhost",
            "https://tauri.localhost"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize services
ipfs_service = IPFSService()
solana_service = SolanaService()
auth_service = AuthService()

# Setup logger
logger = setup_logger("api_server")


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({
                "success": False,
                "error": "Authentication required"
            }), 401
        
        # Remove "Bearer " prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        session = auth_service.validate_session(token)
        if not session:
            return jsonify({
                "success": False,
                "error": "Invalid or expired session"
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler"""
    logger.error(f"Error: {str(error)}")
    return jsonify({
        "success": False,
        "error": str(error)
    }), 500


@app.errorhandler(ValidationError)
def handle_validation_error(error):
    """Validation error handler"""
    logger.warning(f"Validation error: {str(error)}")
    return jsonify({
        "success": False,
        "error": str(error)
    }), 400


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "app": APP_NAME,
        "version": APP_VERSION,
        "ipfs_connected": ipfs_service.check_connection(),
        "solana_connected": solana_service.check_connection()
    })


@app.route('/auth/first-time-check', methods=['GET'])
def first_time_check():
    """Check if this is first time setup and return credentials if available"""
    try:
        welcome_file = get_data_dir() / "WELCOME_CREDENTIALS.txt"
        
        if welcome_file.exists():
            # Read and return the credentials
            with open(welcome_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse username and password from the file
            username = None
            password = None
            for line in content.split('\n'):
                if line.startswith('USERNAME:'):
                    username = line.split('USERNAME:')[1].strip()
                elif line.startswith('PASSWORD:'):
                    password = line.split('PASSWORD:')[1].strip()
            
            if username and password:
                # Delete the file after reading (one-time show)
                welcome_file.unlink()
                logger.info("First-time credentials delivered and file deleted")
                
                return jsonify({
                    "is_first_time": True,
                    "username": username,
                    "password": password,
                    "message": "Save these credentials now! They won't be shown again."
                })
        
        return jsonify({
            "is_first_time": False
        })
    
    except Exception as e:
        logger.error(f"First-time check failed: {str(e)}")
        return jsonify({
            "is_first_time": False,
            "error": str(e)
        }), 500


@app.route('/auth/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            raise ValidationError("Username and password are required")
        
        result = auth_service.login(username, password)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 401


@app.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Logout endpoint"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        result = auth_service.logout(token)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change password endpoint"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        session = auth_service.validate_session(token)
        
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            raise ValidationError("Old password and new password are required")
        
        result = auth_service.change_password(session['username'], old_password, new_password)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Password change failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route('/ipfs/upload', methods=['POST'])
@require_auth
def upload_to_ipfs():
    """Upload file to IPFS"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path:
            raise ValidationError("file_path is required")
        
        result = ipfs_service.upload_file(file_path)
        
        # Save upload record
        save_upload_record(result)
        
        return jsonify(result)
    
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise Exception(f"Upload failed: {str(e)}")


@app.route('/ipfs/download', methods=['POST'])
@require_auth
def download_from_ipfs():
    """Download file from IPFS"""
    try:
        data = request.get_json()
        cid = data.get('cid')
        output_dir = data.get('output_dir', str(get_default_save_dir()))
        
        if not cid:
            raise ValidationError("cid is required")
        
        result = ipfs_service.download_file(cid, output_dir)
        
        # Save download record
        save_download_record(result)
        
        return jsonify(result)
    
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        raise Exception(f"Download failed: {str(e)}")


@app.route('/ipfs/gateway-url', methods=['POST'])
def get_gateway_url():
    """Get IPFS gateway URL for a CID"""
    try:
        data = request.get_json()
        cid = data.get('cid')
        
        if not cid:
            raise ValidationError("cid is required")
        
        url = ipfs_service.get_gateway_url(cid)
        
        return jsonify({
            "success": True,
            "gateway_url": url,
            "cid": cid
        })
    
    except ValidationError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to get gateway URL: {str(e)}")


@app.route('/solana/validate-wallet', methods=['POST'])
@require_auth
def validate_wallet():
    """Validate Solana wallet"""
    try:
        data = request.get_json()
        private_key = data.get('private_key')
        
        if not private_key:
            raise ValidationError("private_key is required")
        
        result = solana_service.validate_wallet(private_key)
        
        return jsonify(result)
    
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Wallet validation failed: {str(e)}")
        raise Exception(f"Wallet validation failed: {str(e)}")


@app.route('/solana/register', methods=['POST'])
@require_auth
def register_on_solana():
    """Register transaction on Solana"""
    try:
        data = request.get_json()
        private_key = data.get('private_key')
        cid = data.get('cid')
        
        if not private_key:
            raise ValidationError("private_key is required")
        if not cid:
            raise ValidationError("cid is required")
        
        result = solana_service.register_transaction(private_key, cid)
        
        # Save transaction record
        save_transaction_record(result)
        
        return jsonify(result)
    
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Transaction registration failed: {str(e)}")
        raise Exception(f"Transaction registration failed: {str(e)}")


@app.route('/config/save-dir', methods=['GET'])
def get_save_directory():
    """Get default save directory"""
    return jsonify({
        "save_dir": str(get_default_save_dir()),
        "data_dir": str(get_data_dir())
    })


def save_upload_record(upload_data: dict):
    """Save upload record to file"""
    try:
        records_dir = get_data_dir() / "uploads"
        records_dir.mkdir(exist_ok=True)
        
        filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        record_file = records_dir / filename
        
        with open(record_file, 'w', encoding='utf-8') as f:
            f.write(f"CID: {upload_data.get('cid')}\n")
            f.write(f"Filename: {upload_data.get('filename')}\n")
            f.write(f"Size: {upload_data.get('size')} bytes\n")
            f.write(f"Gateway URL: {upload_data.get('gateway_url')}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        logger.info(f"Upload record saved: {filename}")
    except Exception as e:
        logger.error(f"Failed to save upload record: {str(e)}")


def save_download_record(download_data: dict):
    """Save download record to file"""
    try:
        records_dir = get_data_dir() / "downloads"
        records_dir.mkdir(exist_ok=True)
        
        filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        record_file = records_dir / filename
        
        with open(record_file, 'w', encoding='utf-8') as f:
            f.write(f"Filename: {download_data.get('filename')}\n")
            f.write(f"Path: {download_data.get('path')}\n")
            f.write(f"Gateway URL: {download_data.get('gateway_url')}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        logger.info(f"Download record saved: {filename}")
    except Exception as e:
        logger.error(f"Failed to save download record: {str(e)}")


def save_transaction_record(tx_data: dict):
    """Save transaction record to file"""
    try:
        records_dir = get_data_dir() / "transactions"
        records_dir.mkdir(exist_ok=True)
        
        filename = f"transaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        record_file = records_dir / filename
        
        with open(record_file, 'w', encoding='utf-8') as f:
            f.write(f"CID: {tx_data.get('cid')}\n")
            f.write(f"Signature: {tx_data.get('signature')}\n")
            f.write(f"Network: {tx_data.get('network')}\n")
            f.write(f"Explorer URL: {tx_data.get('explorer_url')}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        logger.info(f"Transaction record saved: {filename}")
    except Exception as e:
        logger.error(f"Failed to save transaction record: {str(e)}")


def run_server(host='127.0.0.1', port=8765, debug=False):
    """Run the Flask server"""
    logger.info(f"Starting API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)
