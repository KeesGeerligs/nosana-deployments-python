"""Configuration management for Nosana Deployments SDK.

Following the AgentDeploymentConfiguration pattern from the Theoriq Agent SDK.
"""

from __future__ import annotations

import os
from typing import Optional

from solders.keypair import Keypair

from ..utils.env import get_environment, load_wallet_key_from_env
from ..utils.errors import DeploymentError


class DeploymentConfig:
    """Configuration for Nosana Deployment Manager client.
    
    Similar to AgentDeploymentConfiguration in Theoriq SDK, this class
    manages wallet credentials and environment settings.
    """
    
    def __init__(
        self, 
        wallet: Keypair, 
        environment: str = "devnet",
        prefix: str = ""
    ) -> None:
        """Initialize deployment configuration.
        
        Args:
            wallet: Solana wallet keypair for authentication
            environment: Deployment environment ('devnet' or 'mainnet')
            prefix: Optional prefix for environment variable names
        """
        self.wallet = wallet
        self.environment = environment
        self.prefix = prefix
        self.user_id = str(wallet.pubkey())
        self.public_key = wallet.pubkey()
        self.base_url = self._get_base_url()
    
    @classmethod
    def from_env(cls, env_prefix: str = "") -> DeploymentConfig:
        """Create configuration from environment variables.
        
        Expected environment variables:
        - {env_prefix}WALLET_PRIVATE_KEY: Wallet private key (hex string)
        - {env_prefix}ENVIRONMENT: Environment ('devnet' or 'mainnet')
        
        Args:
            env_prefix: Optional prefix for environment variable names
            
        Returns:
            DeploymentConfig instance
            
        Raises:
            DeploymentError: If required environment variables are missing
        """
        try:
            # Load wallet private key
            private_key_hex = load_wallet_key_from_env(env_prefix)
            wallet = Keypair.from_bytes(bytes.fromhex(private_key_hex))
            
            # Load environment
            environment = get_environment(env_prefix)
            
            return cls(wallet, environment, env_prefix)
            
        except ValueError as e:
            raise DeploymentError(
                f"Invalid wallet private key format: {e}",
                error_code="INVALID_WALLET_KEY"
            ) from e
    
    def _get_base_url(self) -> str:
        """Get base URL for the deployment manager API.
        
        Returns:
            Base URL for the specified environment
        """
        urls = {
            "mainnet": "https://deployment-manager.k8s.prd.nos.ci",
            "devnet": "https://deployment-manager.k8s.prd.nos.ci"  # Use prod for now since devnet has issues
        }
        return urls[self.environment]
    
    @property
    def theoriq_uri(self) -> Optional[str]:
        """Get Theoriq URI from environment (if applicable).
        
        Returns:
            Theoriq URI if set in environment
        """
        return os.environ.get(f"{self.prefix}THEORIQ_URI")
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"DeploymentConfig(environment={self.environment}, user_id={self.user_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"DeploymentConfig("
            f"environment={self.environment!r}, "
            f"user_id={self.user_id!r}, "
            f"base_url={self.base_url!r}"
            f")"
        )