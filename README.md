# Nosana Deployments Python SDK

Simple Python SDK for the Nosana Deployment Manager API. **Matches the TypeScript SDK interface exactly** for consistent developer experience.

## 🚀 Quick Start

```python
import os
from nosana_deployments import create_nosana_deployment_client

# Create client - exactly like TypeScript SDK
client = create_nosana_deployment_client(
    manager="https://deployment-manager.k8s.prd.nos.ci",
    key=os.getenv("WALLET_PRIVATE_KEY")  # or hardcode your key
)

# Create deployment
deployment = client.create({
    "name": "My Deployment",
    "market": "7AtiXMSH6R1jjBxrcYjehCkkSF7zvYWte63gwEDBcGHq",
    "ipfs_definition_hash": "QmYourJobDefinitionHash",
    "strategy": "SIMPLE",
    "replicas": 1,
    "timeout": 3600
})

# Use deployment methods - exactly like TypeScript
deployment.start()
deployment.updateReplicaCount(3)
deployment.stop()
```

## 📦 Installation

```bash
pip install pydantic httpx solders
```

## 🎯 API - Identical to TypeScript SDK

### Client Creation
```python
client = create_nosana_deployment_client(
    manager="http://localhost:3000",  # or production URL
    key="WALLET_PRIVATE_KEY"         # env var name or actual key
)
```

### The 4 Main Functions

```python
# 1. Create deployment
deployment = client.create(deployment_body)

# 2. Get deployment by ID  
deployment = client.get("deployment_id")

# 3. List all deployments
deployments = client.list()

# 4. Pipe operations
result = client.pipe(
    "deployment_id_or_create_object",
    lambda d: d.start(),
    lambda d: d.updateReplicaCount(5)
)
```

### Deployment Methods

Once you have a deployment, use these methods **exactly like TypeScript**:

```python
deployment.start()                    # Start deployment
deployment.stop()                     # Stop deployment  
deployment.archive()                  # Archive deployment
deployment.getTasks()                 # Get scheduled tasks
deployment.updateReplicaCount(5)      # Update replicas
deployment.updateTimeout(7200)        # Update timeout
```

## 📋 Complete Example

```python
import os
from nosana_deployments import create_nosana_deployment_client

# Setup
client = create_nosana_deployment_client(
    manager="https://deployment-manager.k8s.prd.nos.ci",
    key=os.getenv("WALLET_PRIVATE_KEY")
)

# Create deployment
deployment = client.create({
    "name": "Data Processing",
    "market": "7AtiXMSH6R1jjBxrcYjehCkkSF7zvYWte63gwEDBcGHq", 
    "ipfs_definition_hash": "QmJobDefinition...",
    "strategy": "SIMPLE",
    "replicas": 2,
    "timeout": 3600
})

# Manage deployment
deployment.start()
print(f"Started: {deployment.name}")

# Scale up
deployment.updateReplicaCount(5)
print("Scaled to 5 replicas")

# List all deployments
deployments = client.list()
for d in deployments:
    print(f"{d.name}: {d.status}")

# Use pipe for chaining
client.pipe(
    deployment.id,
    lambda d: d.updateTimeout(7200),
    lambda d: d.stop()
)
```

## 🔧 Key Configuration

```python
# Different ways to specify the private key:
client = create_nosana_deployment_client(
    manager="https://deployment-manager.k8s.prd.nos.ci",
    key="WALLET_PRIVATE_KEY"  # Environment variable name
)

client = create_nosana_deployment_client(
    manager="https://deployment-manager.k8s.prd.nos.ci", 
    key="3JqLCZfJvyiZqaDzTjr4pAXPqRnAhzgB..."  # Base58 private key
)

client = create_nosana_deployment_client(
    manager="https://deployment-manager.k8s.prd.nos.ci",
    key=keypair_instance  # Solders Keypair object
)
```

## 🎯 TypeScript Compatibility

This Python SDK provides **identical** functionality to the TypeScript SDK:

| TypeScript | Python |
|------------|---------|
| `createNosanaDeploymentClient()` | `create_nosana_deployment_client()` |
| `client.create()` | `client.create()` |
| `client.get()` | `client.get()` |
| `client.list()` | `client.list()` |
| `client.pipe()` | `client.pipe()` |
| `deployment.start()` | `deployment.start()` |
| `deployment.updateReplicaCount()` | `deployment.updateReplicaCount()` |

## 📁 Project Structure

```
nosana_deployments/
├── __init__.py          # Main exports
├── client.py            # Client implementation  
├── auth.py              # Simple wallet auth
└── models/
    ├── base.py          # Base Pydantic model
    └── deployment.py    # Deployment models
```

**Clean and simple** - no bloated code, no unnecessary abstractions.

## 🚀 Ready to Use

The SDK is production-ready and matches the TypeScript SDK exactly. Perfect for teams using both languages.

---

**Built to match the TypeScript SDK interface exactly** ⚡