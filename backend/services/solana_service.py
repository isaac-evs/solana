"""
Solana Service - Handles all Solana blockchain operations
"""
from typing import Dict, Any, Optional
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from backend.config import SOLANA_RPC, SOLANA_NETWORK
from backend.utils.security import validate_private_key
from backend.utils.logger import setup_logger

logger = setup_logger("solana_service")


class SolanaService:
    """Service class for Solana blockchain operations"""
    
    def __init__(self):
        self.rpc_url = SOLANA_RPC
        self.network = SOLANA_NETWORK
        self.client = Client(self.rpc_url)
    
    def validate_wallet(self, private_key: str) -> Dict[str, Any]:
        """
        Validate private key and get wallet information
        
        Args:
            private_key: Base58 encoded private key
            
        Returns:
            Dictionary containing wallet information
            
        Raises:
            Exception: If validation fails
        """
        keypair = None
        try:
            # Validate and sanitize private key
            clean_key = validate_private_key(private_key)
            
            # Create keypair
            keypair = Keypair.from_base58_string(clean_key)
            
            # Get balance
            balance_response = self.client.get_balance(keypair.pubkey())
            balance_lamports = balance_response.value
            balance_sol = balance_lamports / 1e9
            
            # Note: We do NOT return the private key or public key in plaintext for security
            logger.info("Wallet validated successfully")
            
            result = {
                "success": True,
                "balance_sol": balance_sol,
                "balance_lamports": balance_lamports,
                "network": self.network,
                # Only return a truncated version of public key for display
                "public_key_preview": str(keypair.pubkey())[:8] + "..." + str(keypair.pubkey())[-8:]
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Wallet validation failed: {str(e)}")
            raise Exception(f"Invalid wallet: {str(e)}")
        finally:
            # Clear sensitive data from memory
            if keypair:
                del keypair
            del private_key
            if 'clean_key' in locals():
                del clean_key
    
    def register_transaction(self, private_key: str, cid: str) -> Dict[str, Any]:
        """
        Register a transaction on Solana blockchain with IPFS CID
        
        Args:
            private_key: Base58 encoded private key
            cid: IPFS Content Identifier to register
            
        Returns:
            Dictionary containing transaction information
            
        Raises:
            Exception: If transaction fails
        """
        keypair = None
        try:
            # Validate inputs
            clean_key = validate_private_key(private_key)
            
            # Create keypair
            keypair = Keypair.from_base58_string(clean_key)
            
            logger.info(f"Creating transaction for CID: {cid}")
            
            # Check connection
            version = self.client.get_version()
            if not version:
                raise Exception("Cannot connect to Solana network")
            
            # Get recent blockhash
            latest_blockhash = self.client.get_latest_blockhash()
            if not latest_blockhash or not latest_blockhash.value:
                raise Exception("Failed to get blockhash")
            
            recent_blockhash = latest_blockhash.value.blockhash
            
            # Create transaction (self-transfer with minimal lamports)
            # In production, you might want to use a memo program to store the CID
            transaction = Transaction(
                recent_blockhash=recent_blockhash,
                instructions=[
                    transfer(
                        TransferParams(
                            from_pubkey=keypair.pubkey(),
                            to_pubkey=keypair.pubkey(),
                            lamports=1000  # Minimal amount
                        )
                    )
                ]
            )
            
            # Send transaction
            tx_response = self.client.send_transaction(transaction, keypair)
            
            if not tx_response or not tx_response.value:
                raise Exception("Transaction failed")
            
            tx_signature = str(tx_response.value)
            explorer_url = f"https://explorer.solana.com/tx/{tx_signature}?cluster={self.network}"
            
            logger.info(f"Transaction successful. Signature: {tx_signature}")
            
            result = {
                "success": True,
                "signature": tx_signature,
                "explorer_url": explorer_url,
                "network": self.network,
                "cid": cid
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            raise Exception(f"Transaction failed: {str(e)}")
        finally:
            # Clear sensitive data from memory
            if keypair:
                del keypair
            del private_key
            if 'clean_key' in locals():
                del clean_key
    
    def get_balance(self, private_key: str) -> float:
        """
        Get wallet balance in SOL
        
        Args:
            private_key: Base58 encoded private key
            
        Returns:
            Balance in SOL
        """
        try:
            clean_key = validate_private_key(private_key)
            keypair = Keypair.from_base58_string(clean_key)
            balance_response = self.client.get_balance(keypair.pubkey())
            return balance_response.value / 1e9
        except Exception as e:
            logger.error(f"Failed to get balance: {str(e)}")
            raise Exception(f"Failed to get balance: {str(e)}")
    
    def check_connection(self) -> bool:
        """
        Check if Solana RPC is accessible
        
        Returns:
            True if connected, False otherwise
        """
        try:
            version = self.client.get_version()
            return version is not None
        except Exception as e:
            logger.warning(f"Solana connection check failed: {str(e)}")
            return False
