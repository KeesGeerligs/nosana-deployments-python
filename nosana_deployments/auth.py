"""Simple wallet authentication for Nosana Deployments SDK."""

import time
from typing import Dict
from solders.keypair import Keypair
import base58


class WalletAuth:
    """Simple wallet authentication."""
    
    def __init__(self, wallet: Keypair):
        self.wallet = wallet
        self.user_id = str(wallet.pubkey())
    
    def generate_auth_headers(self) -> Dict[str, str]:
        """Generate authentication headers matching TypeScript SDK exactly."""
        # Create base message (same as TypeScript SDK)
        message = "DeploymentsAuthorization"
        
        # Sign message using ed25519 signature (matching nacl.sign.detached in TypeScript)
        message_bytes = message.encode("utf-8")
        
        # Use the private key bytes directly for nacl-style signature
        # This matches the TypeScript SDK's nacl.sign.detached behavior
        import nacl.signing
        import nacl.encoding
        
        # Create signing key from our wallet's private key
        private_key_bytes = bytes(self.wallet.secret())
        signing_key = nacl.signing.SigningKey(private_key_bytes[:32])  # Use first 32 bytes
        
        # Sign the message (detached signature)
        signature = signing_key.sign(message_bytes, encoder=nacl.encoding.RawEncoder).signature
        
        # Encode signature as Base58 (like TypeScript SDK)
        signature_b58 = base58.b58encode(signature).decode('ascii')
        
        # Create timestamp (includeTime: true like TypeScript deployments service)
        timestamp = int(time.time() * 1000)  # Milliseconds like TypeScript
        
        # Create auth string: message:signature_base58:timestamp (matching includeTime: true)
        auth_string = f"{message}:{signature_b58}:{timestamp}"
        
        return {
            "x-user-id": self.user_id,
            "authorization": auth_string
        }