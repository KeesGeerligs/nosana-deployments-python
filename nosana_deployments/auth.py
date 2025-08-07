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
        # Create base message
        message = "DeploymentsAuthorization"
        
        # Sign message (detached signature like TypeScript SDK)
        message_bytes = message.encode("utf-8")
        signature = bytes(self.wallet.sign_message(message_bytes))
        
        # Encode signature as Base58 (like TypeScript SDK)
        signature_b58 = base58.b58encode(signature).decode('ascii')
        
        # Create timestamp
        timestamp = int(time.time() * 1000)  # Milliseconds like TypeScript
        
        # Create auth string: message:signature_base58:timestamp
        auth_string = f"{message}:{signature_b58}:{timestamp}"
        
        return {
            "x-user-id": self.user_id,
            "authorization": auth_string,
            "content-type": "application/json"
        }