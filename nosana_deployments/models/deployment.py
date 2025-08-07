"""Deployment models for Nosana Deployments SDK.

Generated from OpenAPI schema with Pydantic models following
the Theoriq Agent SDK patterns.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

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


class EventCategory(str, Enum):
    """Event category enumeration."""
    
    DEPLOYMENT = "Deployment"
    EVENT = "Event"


class TaskType(str, Enum):
    """Task type enumeration."""
    
    LIST = "LIST"
    EXTEND = "EXTEND"
    STOP = "STOP"


class Job(BaseNosanaModel):
    """Job model representing a deployment job."""
    
    job: str = Field(..., min_length=43, max_length=44, description="Job public key")
    deployment: str = Field(..., min_length=43, max_length=44, description="Deployment public key")
    tx: str = Field(..., description="Transaction signature")
    created_at: datetime = Field(..., description="Job creation timestamp")


class Event(BaseNosanaModel):
    """Event model representing a deployment event."""
    
    category: EventCategory = Field(..., description="Event category")
    deployment_id: str = Field(..., min_length=43, max_length=44, description="Deployment ID", alias="deploymentId")
    type: str = Field(..., description="Event type")
    message: str = Field(..., description="Event message")
    tx: Optional[str] = Field(None, description="Transaction signature")
    created_at: datetime = Field(..., description="Event creation timestamp")


class Task(BaseNosanaModel):
    """Task model representing a scheduled deployment task."""
    
    task: TaskType = Field(..., description="Task type")
    deployment_id: str = Field(..., min_length=43, max_length=44, description="Deployment ID", alias="deploymentId")
    tx: Optional[str] = Field(None, description="Transaction signature")
    due_at: datetime = Field(..., description="Task due timestamp")
    created_at: datetime = Field(..., description="Task creation timestamp")


class Deployment(BaseNosanaModel):
    """Deployment model representing a complete deployment.
    
    Based on the OpenAPI schema with union types for different strategies.
    """
    
    # Core deployment fields
    id: str = Field(..., description="Deployment ID")
    name: str = Field(..., description="Deployment name")
    vault: str = Field(..., min_length=43, max_length=44, description="Vault public key")
    market: str = Field(..., min_length=43, max_length=44, description="Market public key")
    owner: str = Field(..., min_length=43, max_length=44, description="Owner public key")
    status: DeploymentStatus = Field(..., description="Deployment status")
    ipfs_definition_hash: str = Field(..., description="IPFS hash of job definition")
    replicas: int = Field(..., ge=1, description="Number of replicas")
    timeout: int = Field(..., ge=60, description="Timeout in seconds")
    jobs: List[Job] = Field(default_factory=list, description="Associated jobs")
    events: List[Event] = Field(default_factory=list, description="Deployment events")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Strategy-dependent fields
    strategy: DeploymentStrategy = Field(..., description="Deployment strategy")
    schedule: Optional[str] = Field(None, description="Cron expression for scheduled deployments")
    
    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, v: Optional[str], info) -> Optional[str]:
        """Validate schedule field based on strategy."""
        strategy = info.data.get("strategy")
        
        if strategy == DeploymentStrategy.SCHEDULED:
            if not v:
                raise ValueError("Schedule is required when strategy is SCHEDULED")
            # Basic cron validation (6 fields)
            parts = v.strip().split()
            if len(parts) != 6:
                raise ValueError("Schedule must be a valid 6-field cron expression")
        elif v is not None:
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


# Response models for specific operations
class DeploymentStartResponse(BaseNosanaModel):
    """Response model for deployment start operation."""
    
    status: str = Field(..., description="Updated status", pattern="^STARTING$")
    updated_at: datetime = Field(..., description="Update timestamp")


class DeploymentStopResponse(BaseNosanaModel):
    """Response model for deployment stop operation."""
    
    status: str = Field(..., description="Updated status", pattern="^STOPPING$")
    updated_at: datetime = Field(..., description="Update timestamp")


class DeploymentArchiveResponse(BaseNosanaModel):
    """Response model for deployment archive operation."""
    
    status: str = Field(..., description="Updated status", pattern="^ARCHIVED$")
    updated_at: datetime = Field(..., description="Update timestamp")


# Generic status response for backward compatibility
class DeploymentStatusResponse(BaseNosanaModel):
    """Generic response model for status update operations."""
    
    status: Union[DeploymentStatus, str] = Field(..., description="Updated status")
    updated_at: datetime = Field(..., description="Update timestamp")


class DeploymentReplicaResponse(BaseNosanaModel):
    """Response model for replica count update."""
    
    replicas: int = Field(..., ge=1, description="Updated replica count")
    updated_at: datetime = Field(..., description="Update timestamp")


class DeploymentTimeoutResponse(BaseNosanaModel):
    """Response model for timeout update."""
    
    timeout: int = Field(..., description="Updated timeout in seconds")
    updated_at: datetime = Field(..., description="Update timestamp")


class VaultBalanceResponse(BaseNosanaModel):
    """Response model for vault balance."""
    
    SOL: float = Field(..., description="SOL balance")
    NOS: float = Field(..., description="NOS balance")


class VaultWithdrawRequest(BaseNosanaModel):
    """Request model for vault withdrawal."""
    
    SOL: Optional[float] = Field(None, ge=0, description="SOL amount to withdraw")
    NOS: Optional[float] = Field(None, ge=0, description="NOS amount to withdraw")


class VaultWithdrawResponse(BaseNosanaModel):
    """Response model for vault withdrawal."""
    
    transaction: str = Field(..., description="Transaction signature")


class UpdateReplicaRequest(BaseNosanaModel):
    """Request model for updating replica count."""
    
    replicas: int = Field(..., ge=1, description="New replica count")


class UpdateTimeoutRequest(BaseNosanaModel):
    """Request model for updating timeout."""
    
    timeout: int = Field(..., ge=60, description="New timeout in seconds")


class ErrorResponse(BaseNosanaModel):
    """Error response model."""
    
    error: str = Field(..., description="Error message")