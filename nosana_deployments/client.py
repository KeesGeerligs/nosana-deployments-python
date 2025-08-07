"""
Nosana Deployments Client - matches TypeScript SDK structure exactly.
"""

from __future__ import annotations

import os
from typing import Dict, List, Union, Callable, Any, Optional

from solders.keypair import Keypair
import httpx

from .models.deployment import Deployment, DeploymentCreateRequest
from .auth import WalletAuth


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