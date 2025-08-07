#!/usr/bin/env python3
"""
Simple usage examples for Nosana Deployments Python SDK.
Matches the TypeScript SDK structure exactly.
"""

import os
from nosana_deployments import create_nosana_deployment_client

# Example 1: Basic client creation and deployment
def basic_example():
    """Basic deployment creation example."""
    
    # Create client - exactly like TypeScript SDK
    client = create_nosana_deployment_client(
        manager="https://deployment-manager.k8s.prd.nos.ci",
        key=os.getenv("WALLET_PRIVATE_KEY")  # or hardcode: key="your_private_key"
    )
    
    # Create deployment
    deployment = client.create({
        "name": "My Simple Deployment",
        "market": "7AtiXMSH6R1jjBxrcYjehCkkSF7zvYWte63gwEDBcGHq",
        "ipfs_definition_hash": "QmYourJobDefinitionHash",
        "strategy": "SIMPLE",
        "replicas": 1,
        "timeout": 3600
    })
    
    print(f"✅ Created deployment: {deployment.name} ({deployment.id})")
    
    # Use deployment methods - exactly like TypeScript SDK
    deployment.start()
    print("▶️ Started deployment")
    
    deployment.updateReplicaCount(3)
    print("📊 Updated to 3 replicas")
    
    deployment.stop()
    print("⏹️ Stopped deployment")
    
    return deployment


# Example 2: Using the 4 main client functions
def client_functions_example():
    """Demonstrate the 4 main client functions."""
    
    client = create_nosana_deployment_client(
        manager="https://deployment-manager.k8s.prd.nos.ci",
        key=os.getenv("WALLET_PRIVATE_KEY")
    )
    
    # 1. create()
    deployment = client.create({
        "name": "Test Deployment",
        "market": "7AtiXMSH6R1jjBxrcYjehCkkSF7zvYWte63gwEDBcGHq",
        "ipfs_definition_hash": "QmTestHash",
        "strategy": "SIMPLE"
    })
    
    # 2. get()
    same_deployment = client.get(deployment.id)
    assert same_deployment.id == deployment.id
    
    # 3. list()
    deployments = client.list()
    print(f"Found {len(deployments)} deployments")
    
    # 4. pipe() - chain operations
    result = client.pipe(
        deployment.id,
        lambda d: d.start(),
        lambda d: d.updateReplicaCount(2)
    )
    
    return deployments


# Example 3: Scheduled deployment
def scheduled_example():
    """Create a scheduled deployment."""
    
    client = create_nosana_deployment_client(
        manager="https://deployment-manager.k8s.prd.nos.ci", 
        key=os.getenv("WALLET_PRIVATE_KEY")
    )
    
    # Scheduled deployment
    deployment = client.create({
        "name": "Daily Report",
        "market": "7AtiXMSH6R1jjBxrcYjehCkkSF7zvYWte63gwEDBcGHq",
        "ipfs_definition_hash": "QmReportJobHash",
        "strategy": "SCHEDULED",
        "schedule": "0 0 9 * * *",  # Every day at 9 AM
        "replicas": 1,
        "timeout": 1800
    })
    
    # Check tasks
    tasks = deployment.getTasks()
    print(f"📝 Found {len(tasks)} scheduled tasks")
    
    return deployment


if __name__ == "__main__":
    """Run examples."""
    
    if not os.getenv("WALLET_PRIVATE_KEY"):
        print("❌ Please set WALLET_PRIVATE_KEY environment variable")
        exit(1)
    
    print("🚀 Nosana Deployments Python SDK - Simple Examples")
    print("=" * 50)
    
    try:
        print("\n1. Basic Example:")
        basic_example()
        
        print("\n2. Client Functions:")
        client_functions_example()
        
        print("\n3. Scheduled Deployment:")
        scheduled_example()
        
        print("\n✅ All examples completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the API is accessible and your private key is valid")