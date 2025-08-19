"""Simple deployment models for Nosana Deployments SDK."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Any, Dict, TYPE_CHECKING

from pydantic import Field

from .base import BaseNosanaModel

if TYPE_CHECKING:
    from ..client import DeploymentsClient


class DeploymentStatus(str, Enum):
    """Deployment status enumeration from OpenAPI schema."""
    
    DRAFT = "DRAFT"
    ERROR = "ERROR"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    ARCHIVED = "ARCHIVED"


class DeploymentStrategy(str, Enum):
    """Deployment strategy enumeration from OpenAPI schema."""
    
    SIMPLE = "SIMPLE"
    SIMPLE_EXTEND = "SIMPLE-EXTEND"
    SCHEDULED = "SCHEDULED"
    INFINITE = "INFINITE"


# Simple models only - keep just what's needed


class Deployment(BaseNosanaModel):
    """Deployment model matching TypeScript SDK structure exactly."""
    
    # Core fields - backend determines structure so no validation
    id: str
    name: str 
    market: str
    owner: str
    timeout: int
    replicas: int
    status: str  # Use string instead of enum since backend determines
    ipfs_definition_hash: str = Field(alias="ipfs_definition_hash")
    events: List[dict] = Field(default_factory=list)
    jobs: List[dict] = Field(default_factory=list)
    updated_at: datetime
    created_at: datetime
    vault: str
    strategy: str  # Use string instead of enum since backend determines
    schedule: Optional[str] = None
    
    # Private fields for client reference
    _client: Optional[DeploymentsClient] = Field(default=None, exclude=True)
    
    def model_post_init(self, __context: Any) -> None:
        """Initialize methods after model creation."""
        # Methods will be available directly on the instance
        pass
    
    def start(self) -> None:
        """Start the deployment."""
        if not self._client:
            raise RuntimeError("Deployment not attached to client")
        self._client._request("POST", f"/api/deployment/{self.id}/start")
    
    def stop(self) -> None:
        """Stop the deployment."""
        if not self._client:
            raise RuntimeError("Deployment not attached to client")
        self._client._request("POST", f"/api/deployment/{self.id}/stop")
    
    def archive(self) -> None:
        """Archive the deployment."""
        if not self._client:
            raise RuntimeError("Deployment not attached to client")
        self._client._request("PATCH", f"/api/deployment/{self.id}/archive")
    
    def getTasks(self) -> List[Dict[str, Any]]:
        """Get deployment tasks."""
        if not self._client:
            raise RuntimeError("Deployment not attached to client")
        return self._client._request("GET", f"/api/deployment/{self.id}/tasks")
    
    def updateReplicaCount(self, replicas: int) -> None:
        """Update replica count."""
        if not self._client:
            raise RuntimeError("Deployment not attached to client")
        self._client._request("PATCH", f"/api/deployment/{self.id}/update-replica-count", json={"replicas": replicas})
        self.replicas = replicas  # Update local state
    
    def updateTimeout(self, timeout: int) -> None:
        """Update timeout."""
        if not self._client:
            raise RuntimeError("Deployment not attached to client")
        self._client._request("PATCH", f"/api/deployment/{self.id}/update-timeout", json={"timeout": timeout})
        self.timeout = timeout  # Update local state
    
    @property
    def vault_instance(self):
        """Get vault instance for this deployment."""
        if not self._client:
            raise RuntimeError("Deployment not attached to client")
        return self._client.get_vault(self.vault)
    


class DeploymentCreateRequest(BaseNosanaModel):
    """Request model for creating a new deployment."""
    
    name: str
    market: str
    ipfs_definition_hash: str = Field(alias="ipfs_definition_hash")
    replicas: int = Field(default=1)
    timeout: int = Field(default=3600)
    strategy: str
    schedule: Optional[str] = None
    


# Keep it simple - no response models needed