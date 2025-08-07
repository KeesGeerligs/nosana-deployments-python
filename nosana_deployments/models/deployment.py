"""Simple deployment models for Nosana Deployments SDK."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Any, Callable

from pydantic import Field, field_validator

from .base import BaseNosanaModel


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
    """Deployment model matching TypeScript SDK structure."""
    
    # Core fields
    id: str = Field(..., description="Deployment ID")
    name: str = Field(..., description="Deployment name")
    market: str = Field(..., description="Market public key")
    owner: str = Field(..., description="Owner public key")
    timeout: int = Field(..., ge=60, description="Timeout in seconds")
    replicas: int = Field(..., ge=1, description="Number of replicas")
    status: DeploymentStatus = Field(..., description="Deployment status")
    ipfs_definition_hash: str = Field(..., description="IPFS hash of job definition")
    events: List[dict] = Field(default_factory=list, description="Deployment events")
    jobs: List[dict] = Field(default_factory=list, description="Associated jobs")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    vault: dict = Field(..., description="Vault information")
    
    # Strategy-dependent fields
    strategy: DeploymentStrategy = Field(..., description="Deployment strategy")
    schedule: Optional[str] = Field(None, description="Cron expression for scheduled deployments")
    
    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, v: Optional[str], info) -> Optional[str]:
        """Validate schedule field based on strategy."""
        strategy = info.data.get("strategy")
        
        if strategy == DeploymentStrategy.SCHEDULED and not v:
            raise ValueError("Schedule is required when strategy is SCHEDULED")
        elif strategy != DeploymentStrategy.SCHEDULED and v:
            raise ValueError("Schedule can only be set when strategy is SCHEDULED")
            
        return v


class DeploymentCreateRequest(BaseNosanaModel):
    """Request model for creating a new deployment."""
    
    name: str = Field(..., description="Deployment name")
    market: str = Field(..., description="Market public key")
    ipfs_definition_hash: str = Field(..., description="IPFS hash of job definition")
    replicas: int = Field(1, ge=1, description="Number of replicas")
    timeout: int = Field(3600, ge=60, description="Timeout in seconds")
    strategy: DeploymentStrategy = Field(..., description="Deployment strategy")
    schedule: Optional[str] = Field(None, description="Cron expression for scheduled deployments")
    
    @field_validator("schedule")
    @classmethod
    def validate_schedule_create(cls, v: Optional[str], info) -> Optional[str]:
        """Validate schedule field for create request."""
        strategy = info.data.get("strategy")
        
        if strategy == DeploymentStrategy.SCHEDULED and not v:
            raise ValueError("Schedule is required when strategy is SCHEDULED")
        elif strategy != DeploymentStrategy.SCHEDULED and v:
            raise ValueError("Schedule can only be set when strategy is SCHEDULED")
            
        return v


# Keep it simple - no response models needed