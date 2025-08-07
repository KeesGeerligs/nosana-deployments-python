# Nosana Deployments Python SDK

A Python SDK for interacting with the Nosana Deployment Manager API. Built following the design patterns of the [Theoriq Agent SDK](https://github.com/chainbound/theoriq-agent-sdk) with strong typing, caching, and professional code standards.

## 🚀 Quick Start

```python
from nosana_deployments import DeploymentContext, DeploymentStrategy

# One-line setup from environment variables
context = DeploymentContext.from_env()

# Create and start a deployment
deployment = context.create_deployment(
    name="My Deployment",
    market="7AtiXMSH6R1jjBxrcYjehCkkSF7zvYWte63gwEDBcGHq", 
    ipfs_definition_hash="QmYourJobDefinitionHash",
    strategy=DeploymentStrategy.SIMPLE
)

# Start the deployment
context.start_deployment(deployment.id)
print(f"🚀 Deployment {deployment.name} is running!")
```

## 📦 Installation

```bash
pip install nosana-deployments
```

Or with Poetry:
```bash
poetry add nosana-deployments
```

## ⚙️ Configuration

Set these environment variables:

```bash
export WALLET_PRIVATE_KEY="your_solana_wallet_private_key_hex"
export ENVIRONMENT="devnet"  # or "mainnet"
```

Or create a `.env` file:
```env
WALLET_PRIVATE_KEY=your_hex_private_key_here
ENVIRONMENT=devnet
```

## 🎯 Key Features

### ✨ **Really Easy to Use**
- **One-line setup**: `DeploymentContext.from_env()`
- **Strong typing**: Full autocompletion and type safety
- **Intuitive API**: Method names match exactly what you want to do

### 🚄 **High Performance**  
- **TTL Caching**: Automatic caching with expiration for frequently accessed data
- **HTTP Connection Pooling**: Efficient connection reuse
- **Context Managers**: Automatic resource cleanup

### 🔒 **Production Ready**
- **Wallet Authentication**: Automatic Solana message signing
- **Error Handling**: Comprehensive error types with detailed context  
- **Validation**: Pydantic models with field validation
- **Environment Management**: Type-safe environment variable handling

## 📚 Usage Examples

### Basic Deployment Management

```python
from nosana_deployments import DeploymentContext, DeploymentStrategy, DeploymentStatus

# Initialize context
context = DeploymentContext.from_env()

# Create a simple deployment
deployment = context.create_deployment(
    name="Data Processing Job",
    market="7AtiXMSH6R1jjBxrcYjehCkkSF7zvYWte63gwEDBcGHq",
    ipfs_definition_hash="QmJobDefinitionHash...",
    strategy=DeploymentStrategy.SIMPLE,
    replicas=3,
    timeout=3600
)

# Manage the deployment lifecycle
context.start_deployment(deployment.id)
context.update_replica_count(deployment.id, replicas=5)
context.update_timeout(deployment.id, timeout=7200)
context.stop_deployment(deployment.id)
context.archive_deployment(deployment.id)
```

### Scheduled Deployments

```python
# Create a deployment that runs on a schedule
scheduled = context.create_deployment(
    name="Daily Report",
    market="7AtiXMSH6R1jjBxrcYjehCkkSF7zvYWte63gwEDBcGHq",
    ipfs_definition_hash="QmReportJobHash...",
    strategy=DeploymentStrategy.SCHEDULED,
    schedule="0 0 9 * * *",  # Every day at 9 AM
    replicas=1
)
```

### List and Monitor Deployments

```python
# Get all deployments
deployments = context.list_deployments()

for deployment in deployments:
    print(f"{deployment.name}: {deployment.status}")
    
    # Get deployment details (cached for performance)
    details = context.get_deployment(deployment.id)
    
    # Check scheduled tasks
    tasks = context.get_deployment_tasks(deployment.id)
    print(f"  📝 {len(tasks)} scheduled tasks")
```

### Vault Operations

```python
# Check vault balance
balance = context.vault_update_balance("VaultPublicKeyHere...")
print(f"Balance - SOL: {balance.SOL}, NOS: {balance.NOS}")

# Withdraw funds
withdrawal = context.vault_withdraw(
    vault_id="VaultPublicKeyHere...",
    sol=0.1,  # Withdraw 0.1 SOL
    nos=10.0  # Withdraw 10 NOS
)
print(f"Transaction: {withdrawal.transaction}")
```

### Context Manager Pattern

```python
# Automatic resource cleanup
with DeploymentContext.from_env() as context:
    deployments = context.list_deployments()
    # HTTP connections automatically closed when done
```

### Error Handling

```python
from nosana_deployments import (
    DeploymentError, 
    DeploymentAPIError, 
    DeploymentValidationError
)

try:
    deployment = context.create_deployment(
        name="Test",
        market="InvalidKey",  # Will fail validation
        ipfs_definition_hash="QmHash...",
        strategy=DeploymentStrategy.SIMPLE
    )
except DeploymentValidationError as e:
    print(f"Validation failed: {e.field} = {e.value}")
except DeploymentAPIError as e:
    print(f"API error {e.status_code}: {e.message}")
except DeploymentError as e:
    print(f"General error: {e.error_code} - {e.message}")
```

## 📖 API Reference

### DeploymentContext

The main interface for all deployment operations.

#### Methods

- `create_deployment()` - Create a new deployment
- `get_deployment(id)` - Get deployment details  
- `list_deployments()` - List all deployments
- `start_deployment(id)` - Start a deployment
- `stop_deployment(id)` - Stop a deployment
- `archive_deployment(id)` - Archive a deployment
- `update_replica_count(id, replicas)` - Update replica count
- `update_timeout(id, timeout)` - Update timeout
- `get_deployment_tasks(id)` - Get scheduled tasks
- `vault_withdraw(vault_id, sol?, nos?)` - Withdraw from vault
- `vault_update_balance(vault_id)` - Update vault balance

### Models

#### Deployment
- `id: str` - Deployment ID
- `name: str` - Deployment name  
- `status: DeploymentStatus` - Current status
- `strategy: DeploymentStrategy` - Deployment strategy
- `replicas: int` - Number of replicas
- `timeout: int` - Timeout in seconds
- `vault: str` - Vault public key
- `market: str` - Market public key
- `jobs: List[Job]` - Associated jobs
- `events: List[Event]` - Deployment events

#### Enums
- `DeploymentStatus` - DRAFT, RUNNING, STOPPED, etc.
- `DeploymentStrategy` - SIMPLE, SCHEDULED, INFINITE, etc.

## 🛠️ Development

### Setup
```bash
git clone https://github.com/nosana-ci/nosana-deployments-python
cd nosana-deployments-python
poetry install
```

### Testing
```bash
poetry run pytest
```

### Code Quality
```bash
poetry run black .
poetry run ruff check .
poetry run mypy .
```

## 🔗 Related Projects

- [Nosana Deployment Manager](https://deployment-manager.k8s.prd.nos.ci/documentation) - The API this SDK wraps
- [TypeScript SDK](https://gitlab.com/nosana-ci/tools/sdk/typescript) - Reference implementation
- [Theoriq Agent SDK](https://github.com/chainbound/theoriq-agent-sdk) - Design pattern inspiration

## 📄 License

MIT License - see LICENSE file for details.

---

**Made with ❤️ by the Nosana team**

*Following the amazing code standards of the Theoriq Agent SDK*