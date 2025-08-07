#!/usr/bin/env python3
"""
5-minute quick start guide for Nosana Deployments Python SDK.

This demonstrates the absolute simplest way to get started.
"""

from nosana_deployments import DeploymentContext, DeploymentStrategy

# Step 1: One-line setup from environment variables
# (Set WALLET_PRIVATE_KEY and ENVIRONMENT in your shell or .env file)
context = DeploymentContext.from_env()

# Step 2: Create a deployment with just the essentials
deployment = context.create_deployment(
    name="My Test Deployment", 
    market="7AtiXMSH6R1jjBxrcYjehCkkSF7zvYWte63gwEDBcGHq",
    ipfs_definition_hash="QmYourJobDefinitionHash",
    strategy=DeploymentStrategy.SIMPLE
)

print(f"✅ Deployment created: {deployment.id}")

# Step 3: Start it
status = context.start_deployment(deployment.id)
print(f"🚀 Deployment started: {status.status}")

# Step 4: Check your deployments
deployments = context.list_deployments() 
print(f"📋 You have {len(deployments)} total deployments")

# That's it! 🎉