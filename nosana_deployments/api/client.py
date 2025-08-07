"""HTTP client for Nosana Deployments SDK.

Provides authenticated HTTP client with error handling and middleware,
following modern Python patterns with httpx.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx

from ..auth.wallet_auth import WalletAuth
from ..utils.errors import DeploymentAPIError, DeploymentError


class DeploymentHTTPClient:
    """HTTP client for Deployment Manager API.
    
    Provides authenticated requests with automatic error handling
    and response validation.
    """
    
    def __init__(
        self,
        base_url: str,
        auth: WalletAuth,
        timeout: float = 30.0,
        retry_attempts: int = 3
    ) -> None:
        """Initialize HTTP client.
        
        Args:
            base_url: Base URL for the Deployment Manager API
            auth: Wallet authentication manager
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        
        # Create httpx client with default configuration
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={"User-Agent": "nosana-deployments-python/0.1.0"}
        )
    
    def request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> httpx.Response:
        """Make authenticated HTTP request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            json: JSON request body
            params: Query parameters
            headers: Additional headers
            **kwargs: Additional arguments for httpx
            
        Returns:
            HTTP response
            
        Raises:
            DeploymentAPIError: For API-related errors
            DeploymentError: For other errors
        """
        # Ensure path starts with /
        if not path.startswith("/"):
            path = f"/{path}"
        
        # Merge authentication headers
        auth_headers = self.auth.generate_auth_headers()
        if headers:
            auth_headers.update(headers)
        
        # Retry with exponential backoff
        last_exception = None
        for attempt in range(self.retry_attempts + 1):
            try:
                response = self._client.request(
                    method=method,
                    url=path,
                    json=json,
                    params=params,
                    headers=auth_headers,
                    **kwargs
                )
                
                # Handle non-success status codes
                if response.status_code >= 400:
                    # Don't retry client errors (4xx)
                    if 400 <= response.status_code < 500:
                        self._handle_error_response(response)
                    
                    # Retry server errors (5xx) and rate limits (429)
                    if response.status_code >= 500 or response.status_code == 429:
                        if attempt < self.retry_attempts:
                            retry_delay = self._calculate_retry_delay(attempt)
                            time.sleep(retry_delay)
                            continue
                        else:
                            self._handle_error_response(response)
                
                return response
                
            except httpx.HTTPError as e:
                last_exception = DeploymentAPIError(
                    f"HTTP error occurred: {e}",
                    error_code="HTTP_ERROR"
                )
                if attempt < self.retry_attempts:
                    retry_delay = self._calculate_retry_delay(attempt)
                    time.sleep(retry_delay)
                    continue
                else:
                    raise last_exception from e
            except Exception as e:
                raise DeploymentError(
                    f"Unexpected error during request: {e}",
                    error_code="REQUEST_ERROR"
                ) from e
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        else:
            raise DeploymentError(
                "Maximum retry attempts exceeded",
                error_code="MAX_RETRIES_EXCEEDED"
            )
    
    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> httpx.Response:
        """Make GET request."""
        return self.request("GET", path, params=params, headers=headers, **kwargs)
    
    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> httpx.Response:
        """Make POST request."""
        return self.request("POST", path, json=json, headers=headers, **kwargs)
    
    def patch(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> httpx.Response:
        """Make PATCH request."""
        return self.request("PATCH", path, json=json, headers=headers, **kwargs)
    
    def delete(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any
    ) -> httpx.Response:
        """Make DELETE request."""
        return self.request("DELETE", path, headers=headers, **kwargs)
    
    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the API.
        
        Args:
            response: HTTP response with error status
            
        Raises:
            DeploymentAPIError: With details from the response
        """
        try:
            error_data = response.json()
            error_message = error_data.get("error", f"HTTP {response.status_code}")
        except Exception:
            error_data = {}
            error_message = f"HTTP {response.status_code}: {response.text}"
        
        # Handle specific status codes
        if response.status_code == 401:
            error_message = "Unauthorized. Invalid or missing authentication."
        elif response.status_code == 404:
            error_message = "Resource not found."
        elif response.status_code == 500:
            error_message = "Internal server error."
        
        raise DeploymentAPIError(
            error_message,
            status_code=response.status_code,
            response_data=error_data
        )
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay.
        
        Args:
            attempt: Current retry attempt (0-based)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: 1s, 2s, 4s, 8s, etc. (with jitter)
        base_delay = 2 ** attempt
        # Add jitter to avoid thundering herd
        import random
        jitter = random.uniform(0.1, 0.5)
        return min(base_delay + jitter, 30)  # Cap at 30 seconds
    
    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
    
    def __enter__(self) -> DeploymentHTTPClient:
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()