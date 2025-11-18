"""
Security utilities for input validation and sanitization
"""
import os
import re
from pathlib import Path
from typing import Optional
from backend.config import MAX_FILE_SIZE, ALLOWED_FILE_EXTENSIONS


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_file_path(file_path: str) -> Path:
    """
    Validate file path to prevent directory traversal attacks
    
    Args:
        file_path: Path to validate
        
    Returns:
        Path object if valid
        
    Raises:
        ValidationError: If path is invalid or dangerous
    """
    try:
        path = Path(file_path).resolve()
        
        # Check if file exists
        if not path.exists():
            raise ValidationError(f"File does not exist: {file_path}")
        
        # Check if it's actually a file
        if not path.is_file():
            raise ValidationError(f"Path is not a file: {file_path}")
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise ValidationError(f"File too large: {file_size / (1024*1024):.2f}MB (max: {MAX_FILE_SIZE / (1024*1024)}MB)")
        
        # Check file extension
        if path.suffix.lower() not in ALLOWED_FILE_EXTENSIONS:
            raise ValidationError(f"File type not allowed: {path.suffix}")
        
        return path
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"Invalid file path: {str(e)}")


def validate_ipfs_cid(cid: str) -> str:
    """
    Validate IPFS CID format
    
    Args:
        cid: IPFS Content Identifier
        
    Returns:
        Sanitized CID
        
    Raises:
        ValidationError: If CID is invalid
    """
    if not cid:
        raise ValidationError("CID cannot be empty")
    
    # Remove whitespace
    cid = cid.strip()
    
    # Basic CID validation (CIDv0 and CIDv1)
    # CIDv0: starts with Qm, 46 characters, base58
    # CIDv1: starts with b, various lengths, base32
    if len(cid) < 10 or len(cid) > 100:
        raise ValidationError("Invalid CID length")
    
    # Check for valid characters only
    if not re.match(r'^[a-zA-Z0-9]+$', cid):
        raise ValidationError("CID contains invalid characters")
    
    return cid


def validate_private_key(private_key: str) -> str:
    """
    Validate Solana private key format
    
    Args:
        private_key: Base58 encoded private key
        
    Returns:
        Sanitized private key
        
    Raises:
        ValidationError: If private key is invalid
    """
    if not private_key:
        raise ValidationError("Private key cannot be empty")
    
    # Remove whitespace and newlines
    private_key = private_key.replace("\n", "").replace(" ", "").strip()
    
    # Basic length check (Solana private keys are 88 characters in base58)
    if len(private_key) < 80 or len(private_key) > 90:
        raise ValidationError("Invalid private key length")
    
    # Check for valid base58 characters only
    if not re.match(r'^[1-9A-HJ-NP-Za-km-z]+$', private_key):
        raise ValidationError("Private key contains invalid characters")
    
    return private_key


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = Path(filename).name
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename


def validate_directory_path(dir_path: str) -> Path:
    """
    Validate directory path
    
    Args:
        dir_path: Directory path to validate
        
    Returns:
        Path object if valid
        
    Raises:
        ValidationError: If path is invalid
    """
    try:
        path = Path(dir_path).resolve()
        
        if not path.exists():
            raise ValidationError(f"Directory does not exist: {dir_path}")
        
        if not path.is_dir():
            raise ValidationError(f"Path is not a directory: {dir_path}")
        
        # Check if writable
        if not os.access(path, os.W_OK):
            raise ValidationError(f"Directory is not writable: {dir_path}")
        
        return path
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"Invalid directory path: {str(e)}")
