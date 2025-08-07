"""Nosana Deployments Python SDK.

Simple Python SDK for the Nosana Deployment Manager API.

Example:
    ```python
    import os
    from nosana_deployments import create_nosana_deployment_client
    
    # Create client
    client = create_nosana_deployment_client(
        manager="https://deployment-manager.k8s.prd.nos.ci",
        key=os.getenv("WALLET_PRIVATE_KEY")
    )
    
    # Create deployment
    deployment = client.create({
        "name": "My Deployment",
        "market": "7AtiXMSH6R1jjBxrcYjehCkkSF7zvYWte63gwEDBcGHq",
        "ipfs_definition_hash": "QmHash...",
        "strategy": "SIMPLE",
        "replicas": 1,
        "timeout": 3600
    })
    
    # Use deployment methods
    deployment.start()
    deployment.stop()
    ```
"""

from .client import create_nosana_deployment_client
from .models.deployment import Deployment, DeploymentStrategy, DeploymentStatus
from .ipfs import upload_job_to_ipfs
from .vault import create_vault

__version__ = "0.1.0"
__all__ = [
    "create_nosana_deployment_client",
    "Deployment",
    "DeploymentStrategy", 
    "DeploymentStatus",
    "upload_job_to_ipfs",
    "create_vault",
]