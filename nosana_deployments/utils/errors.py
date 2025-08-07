"""Custom exception classes for Nosana Deployments SDK.

Following the error handling patterns from the Theoriq Agent SDK.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class DeploymentError(Exception):
    """Base exception for all Nosana Deployment SDK errors.
    
    Similar to ExecuteRuntimeError in Theoriq SDK, this provides
    a base exception class with optional error codes and messages.
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize a DeploymentError.
        
        Args:
            message: Human-readable error message
            error_code: Optional error code for programmatic handling  
            details: Optional additional error details
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        
        # Construct full error message
        if error_code:
            full_message = f"{error_code}: {message}"
        else:
            full_message = message
            
        super().__init__(full_message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        return self.message


class DeploymentAPIError(DeploymentError):
    """Exception for API-related errors.
    
    Raised when the Deployment Manager API returns an error response
    or when there are network/HTTP issues.
    """
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ) -> None:
        """Initialize a DeploymentAPIError.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code from the API response
            response_data: Raw response data from the API
            error_code: Optional error code from the API
        """
        self.status_code = status_code
        self.response_data = response_data or {}
        
        details = {"status_code": status_code, "response_data": response_data}
        super().__init__(message, error_code, details)


class DeploymentAuthError(DeploymentError):
    """Exception for authentication-related errors.
    
    Raised when wallet authentication fails or when there are
    issues with signing messages or authorization.
    """
    
    def __init__(self, message: str, wallet_address: Optional[str] = None) -> None:
        """Initialize a DeploymentAuthError.
        
        Args:
            message: Human-readable error message
            wallet_address: Wallet address that failed authentication
        """
        self.wallet_address = wallet_address
        
        details = {"wallet_address": wallet_address} if wallet_address else {}
        super().__init__(message, error_code="AUTH_ERROR", details=details)


class DeploymentValidationError(DeploymentError):
    """Exception for data validation errors.
    
    Raised when request data fails validation before sending to the API.
    """
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None) -> None:
        """Initialize a DeploymentValidationError.
        
        Args:
            message: Human-readable error message
            field: Field name that failed validation
            value: Value that failed validation
        """
        self.field = field
        self.value = value
        
        details = {"field": field, "value": value}
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)