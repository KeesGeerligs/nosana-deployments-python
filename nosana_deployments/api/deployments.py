"""Deployment context and operations for Nosana Deployments SDK.

Main interface for deployment operations, following the ExecuteContext 
pattern from the Theoriq Agent SDK.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Union

from solders.keypair import Keypair

from ..auth.wallet_auth import WalletAuth
from ..models.deployment import (
    Deployment,
    DeploymentArchiveResponse,
    DeploymentCreateRequest,
    DeploymentReplicaResponse,
    DeploymentStartResponse,
    DeploymentStatusResponse,
    DeploymentStopResponse,
    DeploymentTimeoutResponse,
    Task,
    UpdateReplicaRequest,
    UpdateTimeoutRequest,
    VaultBalanceResponse,
    VaultWithdrawRequest,
    VaultWithdrawResponse,
)
from ..types.config import DeploymentConfig
from ..utils.cache import TTLCache
from ..utils.errors import DeploymentError, DeploymentValidationError
from .client import DeploymentHTTPClient


class DeploymentContext:
    """Context for deployment operations with authentication and HTTP client.
    
    Similar to ExecuteContext in Theoriq SDK, this class provides the main
    interface for all deployment operations with proper context management.
    """
    
    # Class-level caches following Theoriq patterns
    _deployment_cache: TTLCache[Deployment] = TTLCache(ttl=60, max_size=50)  # 1 minute cache
    _tasks_cache: TTLCache[List[Task]] = TTLCache(ttl=30, max_size=100)  # 30 second cache
    
    def __init__(
        self,
        wallet: Keypair,
        environment: str = "devnet",
        config: Optional[DeploymentConfig] = None
    ) -> None:
        """Initialize deployment context.
        
        Args:
            wallet: Solana wallet keypair for authentication
            environment: Deployment environment ('devnet' or 'mainnet')
            config: Optional deployment configuration (will create if not provided)
        """
        # Create config if not provided
        if config is None:
            config = DeploymentConfig(wallet, environment)
        
        self.config = config
        self.wallet = wallet
        self.environment = environment
        self.user_id = str(wallet.pubkey())
        
        # Initialize authentication
        self.auth = WalletAuth(wallet)
        
        # Initialize HTTP client
        self.client = DeploymentHTTPClient(
            base_url=config.base_url,
            auth=self.auth
        )
    
    @classmethod
    def from_env(cls, env_prefix: str = "") -> DeploymentContext:
        """Create deployment context from environment variables.
        
        Args:
            env_prefix: Optional prefix for environment variable names
            
        Returns:
            DeploymentContext instance configured from environment
        """
        config = DeploymentConfig.from_env(env_prefix)
        return cls(config.wallet, config.environment, config)
    
    # Deployment operations
    def create_deployment(
        self,
        name: str,
        market: str,
        ipfs_definition_hash: str,
        strategy: str,
        replicas: int = 1,
        timeout: int = 3600,
        schedule: Optional[str] = None
    ) -> Deployment:
        """Create a new deployment.
        
        Args:
            name: Deployment name
            market: Market public key
            ipfs_definition_hash: IPFS hash of job definition
            strategy: Deployment strategy ('SIMPLE', 'SCHEDULED', etc.)
            replicas: Number of replicas (default: 1)
            timeout: Timeout in seconds (default: 3600)
            schedule: Cron expression for scheduled deployments
            
        Returns:
            Created deployment
            
        Raises:
            DeploymentValidationError: If request data is invalid
            DeploymentAPIError: If API request fails
        """
        # Create and validate request
        request = DeploymentCreateRequest(
            name=name,
            market=market,
            ipfs_definition_hash=ipfs_definition_hash,
            strategy=strategy,
            replicas=replicas,
            timeout=timeout,
            schedule=schedule
        )
        
        # Send API request
        response = self.client.post("/api/deployment/create", json=request.to_dict())
        return Deployment.model_validate(response.json())
    
    def get_deployment(self, deployment_id: str) -> Deployment:
        """Get deployment by ID.
        
        Uses TTL caching for performance optimization.
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            Deployment details
        """
        # Try cache first
        cached_deployment = self._deployment_cache.get(deployment_id)
        if cached_deployment is not None:
            return cached_deployment
        
        # Fetch from API
        response = self.client.get(f"/api/deployment/{deployment_id}")
        deployment = Deployment.model_validate(response.json())
        
        # Cache the result
        self._deployment_cache.put(deployment_id, deployment)
        
        return deployment
    
    def list_deployments(self) -> List[Deployment]:
        """List all deployments for the authenticated user.
        
        Returns:
            List of deployments
        """
        response = self.client.get("/api/deployments")
        deployments_data = response.json()
        return [Deployment.model_validate(d) for d in deployments_data]
    
    def start_deployment(self, deployment_id: str) -> DeploymentStartResponse:
        """Start an existing deployment.
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            Status response with STARTING status and timestamp
        """
        response = self.client.post(f"/api/deployment/{deployment_id}/start")
        return DeploymentStartResponse.model_validate(response.json())
    
    def stop_deployment(self, deployment_id: str) -> DeploymentStopResponse:
        """Stop a running deployment.
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            Status response with STOPPING status and timestamp
        """
        response = self.client.post(f"/api/deployment/{deployment_id}/stop")
        return DeploymentStopResponse.model_validate(response.json())
    
    def archive_deployment(self, deployment_id: str) -> DeploymentArchiveResponse:
        """Archive a deployment.
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            Status response with ARCHIVED status and timestamp
        """
        response = self.client.patch(f"/api/deployment/{deployment_id}/archive")
        return DeploymentArchiveResponse.model_validate(response.json())
    
    def update_replica_count(self, deployment_id: str, replicas: int) -> DeploymentReplicaResponse:
        """Update the replica count of a deployment.
        
        Args:
            deployment_id: Deployment ID
            replicas: New replica count (must be >= 1)
            
        Returns:
            Response with updated replica count and timestamp
        """
        request = UpdateReplicaRequest(replicas=replicas)
        response = self.client.patch(
            f"/api/deployment/{deployment_id}/update-replica-count",
            json=request.to_dict()
        )
        return DeploymentReplicaResponse.model_validate(response.json())
    
    def update_timeout(self, deployment_id: str, timeout: int) -> DeploymentTimeoutResponse:
        """Update deployment timeout.
        
        Args:
            deployment_id: Deployment ID
            timeout: New timeout in seconds (must be >= 60)
            
        Returns:
            Response with updated timeout and timestamp
        """
        request = UpdateTimeoutRequest(timeout=timeout)
        response = self.client.patch(
            f"/api/deployment/{deployment_id}/update-timeout",
            json=request.to_dict()
        )
        return DeploymentTimeoutResponse.model_validate(response.json())
    
    def get_deployment_tasks(self, deployment_id: str) -> List[Task]:
        """Get scheduled tasks for a deployment.
        
        Uses TTL caching for performance optimization.
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            List of scheduled tasks
        """
        # Try cache first
        cache_key = f"tasks_{deployment_id}"
        cached_tasks = self._tasks_cache.get(cache_key)
        if cached_tasks is not None:
            return cached_tasks
        
        # Fetch from API
        response = self.client.get(f"/api/deployment/{deployment_id}/tasks")
        tasks_data = response.json()
        tasks = [Task.model_validate(task) for task in tasks_data]
        
        # Cache the result
        self._tasks_cache.put(cache_key, tasks)
        
        return tasks
    
    # Vault operations
    def vault_withdraw(
        self,
        vault_id: str,
        sol: Optional[float] = None,
        nos: Optional[float] = None
    ) -> VaultWithdrawResponse:
        """Withdraw from a vault.
        
        Args:
            vault_id: Vault public key
            sol: SOL amount to withdraw (optional)
            nos: NOS amount to withdraw (optional)
            
        Returns:
            Transaction signature for the withdrawal
            
        Raises:
            DeploymentValidationError: If neither SOL nor NOS amounts specified
        """
        if sol is None and nos is None:
            raise DeploymentValidationError(
                "Must specify at least one of SOL or NOS amounts to withdraw"
            )
        
        request = VaultWithdrawRequest(SOL=sol, NOS=nos)
        response = self.client.post(f"/api/vault/{vault_id}/withdraw", json=request.to_dict())
        return VaultWithdrawResponse.model_validate(response.json())
    
    def vault_update_balance(self, vault_id: str) -> VaultBalanceResponse:
        """Update and get vault balance.
        
        Args:
            vault_id: Vault public key
            
        Returns:
            Updated vault balance (SOL and NOS)
        """
        response = self.client.patch(f"/api/vault/{vault_id}/update-balance")
        return VaultBalanceResponse.model_validate(response.json())
    
    # Helper method for chaining operations (similar to Theoriq's pipe pattern)
    def pipe(
        self,
        deployment_id_or_request: Union[str, Dict],
        *operations: callable
    ) -> Deployment:
        """Chain deployment operations.
        
        Similar to the pipe pattern in the TypeScript SDK, allows chaining
        multiple operations on a deployment.
        
        Args:
            deployment_id_or_request: Either a deployment ID or create request data
            *operations: Functions to apply to the deployment
            
        Returns:
            Final deployment state after all operations
        """
        # Get or create deployment
        if isinstance(deployment_id_or_request, str):
            deployment = self.get_deployment(deployment_id_or_request)
        else:
            # Assume it's a dict with create parameters
            deployment = self.create_deployment(**deployment_id_or_request)
        
        # Apply operations
        for operation in operations:
            result = operation(deployment)
            if isinstance(result, Deployment):
                deployment = result
        
        return deployment
    
    # Properties for context information
    @property
    def wallet_address(self) -> str:
        """Get wallet address."""
        return self.user_id
    
    @property
    def base_url(self) -> str:
        """Get API base URL."""
        return self.config.base_url
    
    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self) -> DeploymentContext:
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
    
    def __str__(self) -> str:
        """String representation of deployment context."""
        return f"DeploymentContext(environment={self.environment}, user_id={self.user_id})"