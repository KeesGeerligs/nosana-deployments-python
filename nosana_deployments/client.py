"""
Nosana Deployments Client - matches TypeScript SDK structure exactly.
"""

from __future__ import annotations

import os
from typing import Dict, List, Union, Any, Optional

from solders.keypair import Keypair
import httpx

from .models.deployment import Deployment, DeploymentCreateRequest
from .auth import WalletAuth
from .vault import create_vault


class DeploymentsClient:
    """Simple deployments client matching TypeScript interface exactly."""
    
    def __init__(self, manager: str, wallet: Keypair):
        """Initialize deployments client.
        
        Args:
            manager: Base URL of the deployment manager API
            wallet: Solana wallet keypair for authentication
        """
        self.base_url = manager.rstrip("/")
        self.wallet = wallet
        self.auth = WalletAuth(wallet)
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=30.0,
            headers={"User-Agent": "nosana-deployments-python/0.1.0"}
        )
    
    def _request(self, method: str, path: str, json: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated API request."""
        headers = self.auth.generate_auth_headers()
        
        # Only add content-type when actually sending JSON data
        if json is not None:
            headers["content-type"] = "application/json"
        
        try:
            response = self._client.request(method, path, json=json, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # Enhanced error logging for debugging (opt-in)
            if os.getenv("NOSANA_SDK_DEBUG") and hasattr(e, 'response') and e.response:
                print(f"   🔍 Request details:")
                print(f"      Method: {method}")
                print(f"      URL: {self.base_url}{path}")
                print(f"      Status: {e.response.status_code}")
                print(f"      Request body: {json}")
                print(f"      Request headers: {dict(headers)}")
                try:
                    error_body = e.response.text
                    if error_body:
                        print(f"      Error response: {error_body}")
                except:
                    print(f"      Could not read error response body")
            raise
    
    def create(self, deployment_body: Dict[str, Any]) -> Deployment:
        """Create a new deployment."""
        # Validate request
        request = DeploymentCreateRequest.model_validate(deployment_body)
        
        # Make API call
        data = self._request("POST", "/api/deployment/create", json=request.to_dict())
        deployment_data = data
        
        # Create deployment and attach client reference
        deployment = Deployment.model_validate(deployment_data)
        deployment._client = self
        return deployment
    
    def get(self, deployment_id: str) -> Deployment:
        """Get deployment by ID."""
        data = self._request("GET", f"/api/deployment/{deployment_id}")
        deployment = Deployment.model_validate(data)
        deployment._client = self
        return deployment
    
    def list(self) -> List[Deployment]:
        """List all deployments."""
        data = self._request("GET", "/api/deployments")
        deployments = [Deployment.model_validate(d) for d in data]
        for deployment in deployments:
            deployment._client = self
        return deployments
    
    def pipe(
        self, 
        deployment_id_or_create_object: Union[str, Dict[str, Any]], 
        *actions: Callable[[Deployment], Any]
    ) -> Deployment:
        """Chain deployment operations."""
        # Get or create deployment
        if isinstance(deployment_id_or_create_object, str):
            deployment = self.get(deployment_id_or_create_object)
        else:
            deployment = self.create(deployment_id_or_create_object)
        
        # Apply actions
        for action in actions:
            result = action(deployment)
            if isinstance(result, Deployment):
                deployment = result
        
        return deployment
    
    
    
    
    
    
    def get_vault(self, vault_id: str):
        """Get vault instance for managing vault operations.
        
        Args:
            vault_id: Vault public key
            
        Returns:
            Vault instance with topup, withdraw, getBalance methods
        """
        return create_vault(vault_id, self.wallet, self)
    
    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()


def create_nosana_deployment_client(manager: str, key: Union[str, Keypair]) -> DeploymentsClient:
    """Create Nosana deployment client.
    
    Args:
        manager: Base URL of the deployment manager API
        key: Private key (hex string, base58 string) or Keypair instance
        
    Returns:
        Deployments client instance
    """
    # Handle different key formats
    if isinstance(key, str):
        # Handle environment variable reference
        if key.upper() in os.environ:
            key = os.environ[key.upper()]
        
        # Convert string to Keypair
        if len(key) > 64 and not key.startswith("0x"):
            # Base58 format
            wallet = Keypair.from_base58_string(key)
        else:
            # Hex format
            if key.startswith("0x"):
                key = key[2:]
            wallet = Keypair.from_bytes(bytes.fromhex(key))
    else:
        wallet = key
    
    return DeploymentsClient(manager=manager, wallet=wallet)