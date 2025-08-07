"""Base Pydantic model for Nosana Deployments SDK.

Following the BaseTheoriqModel pattern from the Theoriq Agent SDK.
"""

from __future__ import annotations

from typing import Any, Dict
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseNosanaModel(BaseModel):
    """Base Pydantic model for all Nosana Deployment data structures.
    
    Provides consistent configuration and validation for all models
    in the Nosana Deployments SDK.
    
    Configuration:
        - extra="forbid": Prevents extra fields not defined in the model
        - use_enum_values=True: Uses enum values instead of enum instances in serialization
        - validate_assignment=True: Validates field assignments after model creation
        - alias_generator=to_camel: Converts snake_case to camelCase for API compatibility
        - populate_by_name=True: Allows both snake_case and camelCase field names
    """
    
    model_config = ConfigDict(
        extra="forbid",
        use_enum_values=True,
        validate_assignment=True,
        json_schema_mode="validation",
        strict=False,
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize model to dictionary with camelCase aliases.
        
        Following Theoriq pattern for consistent serialization.
        
        Returns:
            Dictionary representation using camelCase field names
        """
        return self.model_dump(by_alias=True, exclude_none=True)