"""Wallet authentication for Nosana Deployments SDK.

Provides wallet-based authentication for API requests,
following the cryptographic patterns from the Theoriq Agent SDK.
"""

from __future__ import annotations

import time
from typing import Dict

from solders.keypair import Keypair

from ..utils.errors import DeploymentAuthError


class WalletAuth:
    """Wallet-based authentication manager.
    
    Handles message signing and authentication header generation
    for API requests to the Nosana Deployment Manager.
    """
    
    def __init__(self, wallet: Keypair) -> None:
        """Initialize wallet authentication.
        
        Args:
            wallet: Solana wallet keypair for signing
        """
        self.wallet = wallet
        self.user_id = str(wallet.pubkey())
    
    def generate_auth_headers(self, include_timestamp: bool = True) -> Dict[str, str]:
        """Generate authentication headers for API requests.
        
        Creates the required headers for the Deployment Manager API:
        - x-user-id: User's public key
        - authorization: Signed authentication message
        
        Args:
            include_timestamp: Whether to include timestamp in signature
            
        Returns:
            Dictionary containing authentication headers
            
        Raises:
            DeploymentAuthError: If signature generation fails
        """
        try:
            # Generate signed authentication message
            auth_message = self._create_auth_message(include_timestamp)
            
            return {
                "x-user-id": self.user_id,
                "authorization": auth_message,
                "content-type": "application/json"
            }
            
        except Exception as e:
            raise DeploymentAuthError(
                f"Failed to generate authentication headers: {e}",
                wallet_address=self.user_id
            ) from e
    
    def _create_auth_message(self, include_timestamp: bool = True) -> str:
        """Create signed authentication message.
        
        Args:
            include_timestamp: Whether to include current timestamp
            
        Returns:
            Signed authentication message string
        """
        # Create base message
        message = "DeploymentsAuthorization"
        
        if include_timestamp:
            timestamp = int(time.time())
            message = f"{message}:{timestamp}"
        
        # Sign the message
        signature = self.sign_message(message)
        
        # Return formatted authentication string
        return f"{message}:{signature.hex()}"
    
    def sign_message(self, message: str) -> bytes:
        """Sign a message with the wallet's private key.
        
        Args:
            message: Message to sign
            
        Returns:
            Message signature as bytes
            
        Raises:
            DeploymentAuthError: If signing fails
        """
        try:
            message_bytes = message.encode("utf-8")
            signature = bytes(self.wallet.sign_message(message_bytes))
            return signature
            
        except Exception as e:
            raise DeploymentAuthError(
                f"Failed to sign message: {e}",
                wallet_address=self.user_id
            ) from e
    
    def verify_signature(self, message: str, signature: bytes) -> bool:
        """Verify a signature against a message.
        
        Args:
            message: Original message that was signed
            signature: Signature to verify
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            message_bytes = message.encode("utf-8")
            return self.wallet.pubkey().verify(signature, message_bytes)
        except Exception:
            return False
    
    @property
    def public_key_hex(self) -> str:
        """Get wallet public key as hex string.
        
        Returns:
            Public key as hex string with 0x prefix
        """
        return f"0x{bytes(self.wallet.pubkey()).hex()}"
    
    def __str__(self) -> str:
        """String representation of wallet auth."""
        return f"WalletAuth(user_id={self.user_id})"