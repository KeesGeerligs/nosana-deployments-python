"""Nosana Deployments Python SDK.

A Python SDK for interacting with the Nosana Deployment Manager API.
Following the design patterns and code standards of the Theoriq Agent SDK.

Example:
    ```python
    from nosana_deployments import DeploymentContext, DeploymentConfig
    
    # Create config from environment
    config = DeploymentConfig.from_env()
    
    # Create context
    context = DeploymentContext(config.wallet, config.environment)
    
    # Create deployment
    deployment = context.create_deployment(
        name="My Deployment",
        market="7AtiXMSH6R1jjBxrcYjehCkkSF7zvYWte63gwEDBcGHq",
        ipfs_definition_hash="QmHash...",
        strategy="SIMPLE"
    )
    ```
"""

from .api.deployments import DeploymentContext
from .models.deployment import (
    Deployment,
    DeploymentArchiveResponse,
    DeploymentCreateRequest,
    DeploymentStartResponse,
    DeploymentStatus,
    DeploymentStatusResponse,
    DeploymentStopResponse,
    DeploymentStrategy,
    VaultBalanceResponse,
    VaultWithdrawResponse,
)
from .types.config import DeploymentConfig
from .utils.errors import DeploymentError

__version__ = "0.1.0"
__all__ = [
    "DeploymentContext",
    "Deployment",
    "DeploymentArchiveResponse",
    "DeploymentCreateRequest",
    "DeploymentStartResponse",
    "DeploymentStatus",
    "DeploymentStatusResponse",
    "DeploymentStopResponse",
    "DeploymentStrategy",
    "DeploymentConfig",
    "DeploymentError",
    "VaultBalanceResponse",
    "VaultWithdrawResponse",
]