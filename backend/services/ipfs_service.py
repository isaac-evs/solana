"""
IPFS Service - Handles all IPFS operations
"""
import ipfshttpclient
import zipfile
import shutil
from pathlib import Path
from typing import Dict, Any
from backend.config import IPFS_API_ADDR, IPFS_GATEWAY, IPFS_TIMEOUT
from backend.utils.security import validate_file_path, validate_ipfs_cid, sanitize_filename
from backend.utils.logger import setup_logger

logger = setup_logger("ipfs_service")


class IPFSService:
    """Service class for IPFS operations"""
    
    def __init__(self):
        self.gateway = IPFS_GATEWAY
        self.timeout = IPFS_TIMEOUT
    
    def upload_file(self, file_path: str) -> Dict[str, Any]:
        """
        Upload file to IPFS
        
        Args:
            file_path: Path to file to upload
            
        Returns:
            Dictionary containing CID and metadata
            
        Raises:
            Exception: If upload fails
        """
        try:
            # Validate file path
            validated_path = validate_file_path(file_path)
            
            logger.info(f"Uploading file to IPFS: {validated_path.name}")
            
            # Connect to IPFS and upload
            with ipfshttpclient.connect(IPFS_API_ADDR, timeout=self.timeout) as client:
                result = client.add(str(validated_path))
                
                cid = result["Hash"]
                file_size = result.get("Size", validated_path.stat().st_size)
                
                logger.info(f"File uploaded successfully. CID: {cid}")
                
                return {
                    "success": True,
                    "cid": cid,
                    "filename": validated_path.name,
                    "size": file_size,
                    "gateway_url": f"{self.gateway}{cid}"
                }
        
        except Exception as e:
            logger.error(f"Failed to upload file: {str(e)}")
            raise Exception(f"IPFS upload failed: {str(e)}")
    
    def download_file(self, cid: str, output_dir: str) -> Dict[str, Any]:
        """
        Download file from IPFS and create a zip archive
        
        Args:
            cid: IPFS Content Identifier
            output_dir: Directory to save downloaded file
            
        Returns:
            Dictionary containing download metadata
            
        Raises:
            Exception: If download fails
        """
        try:
            # Validate CID
            validated_cid = validate_ipfs_cid(cid)
            
            # Validate output directory
            output_path = Path(output_dir).resolve()
            if not output_path.exists():
                raise Exception(f"Output directory does not exist: {output_dir}")
            
            logger.info(f"Downloading from IPFS. CID: {validated_cid}")
            
            # Connect to IPFS and download
            with ipfshttpclient.connect(IPFS_API_ADDR, timeout=self.timeout) as client:
                client.get(validated_cid, target=str(output_path))
                
                # Handle downloaded file
                downloaded_dir = output_path / validated_cid
                
                if downloaded_dir.exists() and downloaded_dir.is_dir():
                    files = list(downloaded_dir.iterdir())
                    
                    if files:
                        # Create zip file
                        zip_filename = f"{validated_cid}.zip"
                        zip_path = output_path / zip_filename
                        
                        # Handle duplicate filenames
                        counter = 1
                        while zip_path.exists():
                            zip_filename = f"{validated_cid}_{counter}.zip"
                            zip_path = output_path / zip_filename
                            counter += 1
                        
                        # Create the zip archive
                        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            for file_path in files:
                                if file_path.is_file():
                                    zipf.write(file_path, file_path.name)
                                elif file_path.is_dir():
                                    # Add directory and all its contents
                                    for item in file_path.rglob('*'):
                                        if item.is_file():
                                            arcname = item.relative_to(file_path.parent)
                                            zipf.write(item, arcname)
                        
                        # Clean up downloaded directory
                        shutil.rmtree(downloaded_dir)
                        
                        logger.info(f"File downloaded and zipped successfully: {zip_filename}")
                        
                        return {
                            "success": True,
                            "filename": zip_filename,
                            "path": str(zip_path),
                            "gateway_url": f"{self.gateway}{validated_cid}"
                        }
                    else:
                        raise Exception("Downloaded directory is empty")
                else:
                    raise Exception("Download did not create expected directory")
        
        except Exception as e:
            logger.error(f"Failed to download file: {str(e)}")
            raise Exception(f"IPFS download failed: {str(e)}")
    
    def get_gateway_url(self, cid: str) -> str:
        """
        Get gateway URL for a CID
        
        Args:
            cid: IPFS Content Identifier
            
        Returns:
            Gateway URL
        """
        validated_cid = validate_ipfs_cid(cid)
        return f"{self.gateway}{validated_cid}"
    
    def check_connection(self) -> bool:
        """
        Check if IPFS daemon is running
        
        Returns:
            True if connected, False otherwise
        """
        try:
            with ipfshttpclient.connect(IPFS_API_ADDR, timeout=5) as client:
                client.version()
                return True
        except Exception as e:
            logger.warning(f"IPFS connection check failed: {str(e)}")
            return False
