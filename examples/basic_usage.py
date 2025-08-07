#!/usr/bin/env python3
"""
Basic usage examples for Nosana Deployments Python SDK.

Demonstrates the most common patterns for deployment management.
"""

import os
from nosana_deployments import DeploymentContext, DeploymentConfig, DeploymentStrategy

# Example 1: Simple deployment creation
def create_simple_deployment():
    """Create a basic deployment from environment variables."""
    
    # Set up environment variables (normally done in .env or shell)
    # os.environ["WALLET_PRIVATE_KEY"] = "your_hex_private_key_here"
    # os.environ["ENVIRONMENT"] = "devnet"  # or "mainnet"
    
    # Create context from environment - one line setup
    context = DeploymentContext.from_env()
    
    # Create a simple deployment - strongly typed parameters
    deployment = context.create_deployment(
        name="My First Deployment",
        market="7AtiXMSH6R1jjBxrcYjehCkkSF7zvYWte63gwEDBcGHq",
        ipfs_definition_hash="QmYourJobDefinitionHashHere...",
        strategy=DeploymentStrategy.SIMPLE,  # Enum for type safety
        replicas=2,
        timeout=3600  # 1 hour
    )
    
    print(f"✅ Created deployment: {deployment.id}")
    print(f"   Status: {deployment.status}")
    print(f"   Vault: {deployment.vault}")
    
    return deployment


# Example 2: Scheduled deployment with cron
def create_scheduled_deployment():
    """Create a scheduled deployment that runs on a cron schedule."""
    
    context = DeploymentContext.from_env()
    
    # Create scheduled deployment - requires cron expression
    deployment = context.create_deployment(
        name="Daily Report Generator",
        market="7AtiXMSH6R1jjBxrcYjehCkkSF7zvYWte63gwEDBcGHq",
        ipfs_definition_hash="QmScheduledJobHashHere...",
        strategy=DeploymentStrategy.SCHEDULED,
        schedule="0 0 9 * * *",  # Every day at 9 AM
        replicas=1,
        timeout=1800  # 30 minutes
    )
    
    print(f"📅 Created scheduled deployment: {deployment.id}")
    print(f"   Schedule: {deployment.schedule}")
    
    return deployment


# Example 3: Managing deployment lifecycle
def manage_deployment_lifecycle(deployment_id: str):
    """Demonstrate full deployment lifecycle management."""
    
    context = DeploymentContext.from_env()
    
    # Get deployment details (uses caching for performance)
    deployment = context.get_deployment(deployment_id)
    print(f"📋 Deployment {deployment.name} is {deployment.status}")
    
    # Start the deployment
    start_response = context.start_deployment(deployment_id)
    print(f"▶️  Started deployment at {start_response.updated_at}")
    
    # Update replica count
    replica_response = context.update_replica_count(deployment_id, replicas=5)
    print(f"📊 Updated to {replica_response.replicas} replicas")
    
    # Get scheduled tasks (also uses caching)
    tasks = context.get_deployment_tasks(deployment_id)
    print(f"📝 Found {len(tasks)} scheduled tasks")
    
    # Stop the deployment
    stop_response = context.stop_deployment(deployment_id)
    print(f"⏹️  Stopped deployment at {stop_response.updated_at}")
    
    # Archive when done
    archive_response = context.archive_deployment(deployment_id)
    print(f"📦 Archived deployment at {archive_response.updated_at}")


# Example 4: Context manager pattern for resource cleanup
def context_manager_example():
    """Use context manager for automatic resource cleanup."""
    
    # Automatically closes HTTP connections when done
    with DeploymentContext.from_env() as context:
        deployments = context.list_deployments()
        print(f"Found {len(deployments)} deployments:")
        
        for deployment in deployments:
            print(f"  • {deployment.name} ({deployment.status})")
            
        # HTTP client automatically closed when exiting context


# Example 5: Vault operations
def vault_operations_example():
    """Demonstrate vault balance and withdrawal operations."""
    
    context = DeploymentContext.from_env()
    
    # Assume we have a vault ID from a deployment
    vault_id = "YourVaultPublicKeyHere..."
    
    # Update and get vault balance
    balance = context.vault_update_balance(vault_id)
    print(f"💰 Vault balance - SOL: {balance.SOL}, NOS: {balance.NOS}")
    
    # Withdraw SOL (if balance available)
    if balance.SOL and balance.SOL > 0.1:
        withdraw_response = context.vault_withdraw(
            vault_id=vault_id,
            sol=0.05  # Withdraw 0.05 SOL
        )
        print(f"💸 Withdrawal transaction: {withdraw_response.transaction}")


# Example 6: Error handling patterns
def error_handling_example():
    """Demonstrate proper error handling."""
    
    from nosana_deployments import DeploymentError, DeploymentAPIError, DeploymentValidationError
    
    try:
        context = DeploymentContext.from_env()
        
        # This will fail validation - strategy and schedule mismatch
        deployment = context.create_deployment(
            name="Invalid Deployment",
            market="InvalidMarketKey",  # Too short
            ipfs_definition_hash="QmValid...",
            strategy=DeploymentStrategy.SIMPLE,
            schedule="0 0 * * * *"  # Schedule without SCHEDULED strategy
        )
        
    except DeploymentValidationError as e:
        print(f"❌ Validation error: {e.message}")
        print(f"   Field: {e.field}, Value: {e.value}")
        
    except DeploymentAPIError as e:
        print(f"🌐 API error: {e.message}")
        print(f"   Status: {e.status_code}")
        
    except DeploymentError as e:
        print(f"🚫 General error: {e.message}")
        print(f"   Code: {e.error_code}")


if __name__ == "__main__":
    """Run examples (make sure environment variables are set first)."""
    
    print("🚀 Nosana Deployments SDK Examples")
    print("=" * 40)
    
    try:
        # Example 1: Create simple deployment
        print("\n1. Creating simple deployment...")
        deployment = create_simple_deployment()
        
        # Example 3: Manage lifecycle (using the deployment we just created)
        print("\n2. Managing deployment lifecycle...")
        manage_deployment_lifecycle(deployment.id)
        
        # Example 4: Context manager
        print("\n3. Using context manager...")
        context_manager_example()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("Make sure to set WALLET_PRIVATE_KEY and ENVIRONMENT variables!")