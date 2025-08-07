"""Environment variable utilities for Nosana Deployments SDK.

Provides consistent environment variable handling following 
the patterns from the Theoriq Agent SDK.
"""

from __future__ import annotations

import os
from typing import Callable, Optional, Type, TypeVar

from .errors import DeploymentError

T = TypeVar("T")


class EnvVariableValueException(DeploymentError):
    """Exception for environment variable type conversion errors."""
    
    def __init__(self, *, name: str, value: str, expected_type: Type) -> None:
        self.name = name
        super().__init__(
            f"Environment variable {name} value `{value}` has invalid type, expected: {expected_type}",
            error_code="ENV_VAR_INVALID_TYPE"
        )


def _read_env_required(name: str, converter: Callable[[str], T]) -> T:
    """Read required environment variable with type conversion.
    
    Args:
        name: Environment variable name
        converter: Function to convert string value to desired type
        
    Returns:
        Converted environment variable value
        
    Raises:
        DeploymentError: If variable not found or conversion fails
    """
    value = os.environ.get(name)
    if value is None:
        raise DeploymentError(
            f"Required environment variable '{name}' not found",
            error_code="ENV_VAR_MISSING"
        )
    
    try:
        return converter(value)
    except (ValueError, TypeError) as e:
        raise EnvVariableValueException(
            name=name, 
            value=value, 
            expected_type=type(converter(""))
        ) from e


def _read_env_optional(name: str, default: Optional[T], converter: Callable[[str], T]) -> Optional[T]:
    """Read optional environment variable with type conversion.
    
    Args:
        name: Environment variable name
        default: Default value if variable not found
        converter: Function to convert string value to desired type
        
    Returns:
        Converted environment variable value or default
    """
    value = os.environ.get(name)
    if value is None:
        return default
    
    try:
        return converter(value)
    except (ValueError, TypeError):
        return default


def _bool_converter(name: str) -> Callable[[str], bool]:
    """Create boolean converter for environment variables."""
    def converter(value: str) -> bool:
        lower_value = value.lower()
        if lower_value in ("true", "1", "yes", "on"):
            return True
        elif lower_value in ("false", "0", "no", "off"):
            return False
        else:
            raise ValueError(f"Invalid boolean value for {name}: {value}")
    return converter


# Type-safe environment variable readers following Theoriq patterns
def must_read_env_str(name: str) -> str:
    """Read required string environment variable.
    
    Args:
        name: Environment variable name
        
    Returns:
        Environment variable value
        
    Raises:
        DeploymentError: If variable not found
    """
    return _read_env_required(name, lambda x: x)


def read_env_str(name: str, default: Optional[str] = None) -> Optional[str]:
    """Read optional string environment variable.
    
    Args:
        name: Environment variable name
        default: Default value if variable not found
        
    Returns:
        Environment variable value or default
    """
    return _read_env_optional(name, default, lambda x: x)


def must_read_env_int(name: str) -> int:
    """Read required integer environment variable.
    
    Args:
        name: Environment variable name
        
    Returns:
        Environment variable value as integer
        
    Raises:
        DeploymentError: If variable not found or invalid
    """
    return _read_env_required(name, int)


def read_env_int(name: str, default: Optional[int] = None) -> Optional[int]:
    """Read optional integer environment variable.
    
    Args:
        name: Environment variable name
        default: Default value if variable not found
        
    Returns:
        Environment variable value as integer or default
    """
    return _read_env_optional(name, default, int)


def must_read_env_bool(name: str) -> bool:
    """Read required boolean environment variable.
    
    Args:
        name: Environment variable name
        
    Returns:
        Environment variable value as boolean
        
    Raises:
        DeploymentError: If variable not found or invalid
    """
    return _read_env_required(name, _bool_converter(name))


def read_env_bool(name: str, default: Optional[bool] = None) -> Optional[bool]:
    """Read optional boolean environment variable.
    
    Args:
        name: Environment variable name
        default: Default value if variable not found
        
    Returns:
        Environment variable value as boolean or default
    """
    return _read_env_optional(name, default, _bool_converter(name))


# Legacy functions for backward compatibility
def get_env_var(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """Get environment variable with optional default and validation.
    
    Args:
        name: Environment variable name
        default: Default value if variable not found
        required: If True, raises DeploymentError if variable not found
        
    Returns:
        Environment variable value or default
        
    Raises:
        DeploymentError: If required=True and variable not found
    """
    if required:
        return must_read_env_str(name)
    else:
        return read_env_str(name, default)


def load_wallet_key_from_env(env_prefix: str = "") -> str:
    """Load wallet private key from environment.
    
    Looks for {env_prefix}WALLET_PRIVATE_KEY in environment.
    Supports both base58 (Solana format) and hex formats.
    
    Args:
        env_prefix: Optional prefix for environment variable name
        
    Returns:
        Wallet private key as hex string
        
    Raises:
        DeploymentError: If wallet key not found in environment
    """
    key_var = f"{env_prefix}WALLET_PRIVATE_KEY"
    private_key = must_read_env_str(key_var)
    
    # Handle base58 format (Solana standard)
    if len(private_key) > 64 and not private_key.startswith("0x"):
        try:
            import base58
            decoded_bytes = base58.b58decode(private_key)
            private_key = decoded_bytes.hex()
        except ImportError:
            # Fallback: try with solders if available
            try:
                from solders.keypair import Keypair
                keypair = Keypair.from_base58_string(private_key)
                private_key = bytes(keypair).hex()
            except Exception as e:
                raise DeploymentError(
                    f"Unable to decode base58 private key. Install base58 package or provide hex format: {e}",
                    error_code="INVALID_KEY_FORMAT"
                ) from e
        except Exception as e:
            raise DeploymentError(
                f"Invalid base58 private key format: {e}",
                error_code="INVALID_BASE58_KEY"
            ) from e
    else:
        # Handle hex format
        if private_key.startswith("0x"):
            private_key = private_key[2:]
    
    return private_key


def get_environment(env_prefix: str = "") -> str:
    """Get deployment environment from environment variables.
    
    Args:
        env_prefix: Optional prefix for environment variable name
        
    Returns:
        Environment name ('devnet' or 'mainnet'), defaults to 'devnet'
    """
    env_var = f"{env_prefix}ENVIRONMENT"
    environment = read_env_str(env_var, default="devnet")
    
    # Validate environment value
    if environment not in ("devnet", "mainnet"):
        raise DeploymentError(
            f"Invalid environment '{environment}'. Must be 'devnet' or 'mainnet'",
            error_code="INVALID_ENVIRONMENT"
        )
    
    return environment