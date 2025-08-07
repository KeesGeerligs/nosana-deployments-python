"""
Nosana Deployments Client - matches TypeScript SDK structure exactly.
"""

from __future__ import annotations

import os
from typing import Dict, List, Union, Callable, Any, Optional

from solders.keypair import Keypair
import httpx
import requests

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
        response = self._client.request(method, path, json=json, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def create(self, deployment_body: Dict[str, Any]) -> Deployment:
        """Create a new deployment."""
        # Validate request
        request = DeploymentCreateRequest.model_validate(deployment_body)
        
        # Make API call
        data = self._request("POST", "/api/deployment/create", json=request.to_dict())
        deployment_data = data
        
        # Create deployment with methods attached
        deployment = Deployment.model_validate(deployment_data)
        self._attach_methods(deployment)
        return deployment
    
    def get(self, deployment_id: str) -> Deployment:
        """Get deployment by ID."""
        data = self._request("GET", f"/api/deployment/{deployment_id}")
        deployment = Deployment.model_validate(data)
        self._attach_methods(deployment)
        return deployment
    
    def list(self) -> List[Deployment]:
        """List all deployments."""
        data = self._request("GET", "/api/deployments")
        deployments = [Deployment.model_validate(d) for d in data]
        for deployment in deployments:
            self._attach_methods(deployment)
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
    
    def _attach_methods(self, deployment: Deployment) -> None:
        """Attach methods to deployment instance."""
        # Store reference to client for methods
        deployment.__dict__['_client'] = self
        
        # Attach methods that match TypeScript SDK exactly
        deployment.__dict__['start'] = lambda: self._start_deployment(deployment.id)
        deployment.__dict__['stop'] = lambda: self._stop_deployment(deployment.id)
        deployment.__dict__['archive'] = lambda: self._archive_deployment(deployment.id)
        deployment.__dict__['getTasks'] = lambda: self._get_deployment_tasks(deployment.id)
        deployment.__dict__['updateReplicaCount'] = lambda replicas: self._update_replica_count(deployment.id, replicas)
        deployment.__dict__['updateTimeout'] = lambda timeout: self._update_timeout(deployment.id, timeout)
        deployment.__dict__['updateVaultBalance'] = lambda: self.update_vault_balance(deployment.vault)
        
        # Attach vault instance
        deployment.__dict__['vault_instance'] = lambda: self.get_vault(deployment.vault)
    
    def _start_deployment(self, deployment_id: str) -> None:
        """Start deployment."""
        self._request("POST", f"/api/deployment/{deployment_id}/start")
    
    def _stop_deployment(self, deployment_id: str) -> None:
        """Stop deployment."""
        self._request("POST", f"/api/deployment/{deployment_id}/stop")
    
    def _archive_deployment(self, deployment_id: str) -> None:
        """Archive deployment."""
        self._request("PATCH", f"/api/deployment/{deployment_id}/archive")
    
    def _get_deployment_tasks(self, deployment_id: str) -> List[Dict[str, Any]]:
        """Get deployment tasks."""
        return self._request("GET", f"/api/deployment/{deployment_id}/tasks")
    
    def _update_replica_count(self, deployment_id: str, replicas: int) -> None:
        """Update replica count."""
        self._request("PATCH", f"/api/deployment/{deployment_id}/update-replica-count", json={"replicas": replicas})
    
    def _update_timeout(self, deployment_id: str, timeout: int) -> None:
        """Update timeout."""
        self._request("PATCH", f"/api/deployment/{deployment_id}/update-timeout", json={"timeout": timeout})
    
    def update_vault_balance(self, vault_id: str) -> Dict[str, float]:
        """Update vault balance from blockchain.
        
        Args:
            vault_id: Vault public key
            
        Returns:
            Dictionary with SOL and NOS balances
        """
        return self._request("PATCH", f"/api/vault/{vault_id}/update-balance")
    
    def topup_vault(self, vault_id: str, sol_amount: float = 0.0, nos_amount: float = 0.0) -> str:
        """Transfer SOL and/or NOS from user wallet to vault.
        
        Args:
            vault_id: Target vault public key
            sol_amount: Amount of SOL to transfer (e.g. 0.01 = 0.01 SOL)
            nos_amount: Amount of NOS to transfer (e.g. 10 = 10 NOS)
            
        Returns:
            Transaction signature
        """
        if sol_amount <= 0 and nos_amount <= 0:
            raise ValueError("Must specify positive amount for SOL or NOS")
        
        # For now, implement SOL transfer (simpler)
        if sol_amount > 0:
            return self._transfer_sol_to_vault(vault_id, sol_amount)
        else:
            raise NotImplementedError("NOS transfer not yet implemented")
    
    def _transfer_sol_to_vault(self, vault_id: str, sol_amount: float) -> str:
        """Transfer SOL from user wallet to vault using Solana RPC.
        
        Args:
            vault_id: Target vault public key
            sol_amount: SOL amount to transfer
            
        Returns:
            Transaction signature
        """
        try:
            # Convert SOL to lamports
            lamports = int(sol_amount * 1_000_000_000)
            
            # Create transfer instruction
            from_pubkey = Pubkey.from_string(str(self.wallet.pubkey()))
            to_pubkey = Pubkey.from_string(vault_id)
            
            # Use public Solana RPC (you may want to use a dedicated RPC endpoint)
            rpc_url = "https://api.mainnet-beta.solana.com"
            
            # Get recent blockhash
            response = requests.post(rpc_url, json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getLatestBlockhash"
            })
            
            if response.status_code != 200:
                raise Exception(f"Failed to get blockhash: {response.status_code}")
            
            result = response.json()
            if "error" in result:
                raise Exception(f"RPC error: {result['error']}")
                
            blockhash = result["result"]["value"]["blockhash"]
            
            # Create transfer instruction
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=from_pubkey,
                    to_pubkey=to_pubkey, 
                    lamports=lamports
                )
            )
            
            # This is a simplified implementation
            # A full implementation would need to:
            # 1. Create a proper transaction with the instruction
            # 2. Sign it with the wallet
            # 3. Send it to the network
            # 4. Wait for confirmation
            
            raise NotImplementedError(
                "Direct SOL transfer requires more complex transaction building. "
                "Please fund the vault manually for now. "
                f"Send {sol_amount} SOL to: {vault_id}"
            )
            
        except Exception as e:
            raise Exception(f"Vault topup failed: {e}")
    
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