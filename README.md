# Nosana Deployments Python SDK

Simple Python SDK for the Nosana Deployment Manager API. **Matches the TypeScript SDK interface exactly** for consistent developer experience.

## 🚀 Quick Start

```python
from nosana_deployments import create_nosana_deployment_client, upload_job_to_ipfs

# 1. Upload job definition to IPFS
job_definition = {
    "ops": [{
        "id": "pytorch-jupyter",
        "type": "container/run", 
        "args": {
            "image": "docker.io/nosana/pytorch-jupyter:2.0.0",
            "cmd": ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser"],
            "gpu": True,
            "expose": 8888
        }
    }],
    "type": "container",
    "version": "0.1"
}

ipfs_hash = upload_job_to_ipfs(job_definition)

# 2. Create client - exactly like TypeScript SDK
client = create_nosana_deployment_client(
    manager="https://deployment-manager.k8s.prd.nos.ci",
    key="your_wallet_private_key"
)

# 3. Create deployment
deployment = client.create({
    "name": "PyTorch Jupyter Lab",
    "market": "97G9NnvBDQ2WpKu6fasoMsAKmfj63C9rhysJnkeWodAf",
    "ipfs_definition_hash": ipfs_hash,
    "strategy": "SIMPLE",
    "replicas": 1,
    "timeout": 3600
})

# 4. Fund vault (manual step)
print(f"Fund this vault: {deployment.vault}")
print(f"https://solscan.io/account/{deployment.vault}")

# 5. Check balance and start
balance = deployment.updateVaultBalance()  
deployment.start()  # Once funded
```

## 🎯 Usage Scripts

### Deploy a Job

```bash
export WALLET_PRIVATE_KEY="your_base58_private_key"
python deploy_job.py
```

This demonstrates the complete deployment workflow: create deployment, fund vault, start job.

### Withdraw Funds

```bash
export WALLET_PRIVATE_KEY="your_base58_private_key"  
python withdraw_funds.py
```

This finds all your vaults with funds and withdraws them back to your wallet.

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
deployment.updateVaultBalance()       # Refresh vault balance from blockchain
```

### IPFS Upload

Upload job definitions to IPFS using Pinata (same as TypeScript SDK):

```python
from nosana_deployments import upload_job_to_ipfs

# Upload job definition
ipfs_hash = upload_job_to_ipfs({
    "ops": [{"id": "my-job", "type": "container/run", "args": {...}}],
    "type": "container",
    "version": "0.1"
})

# Use in deployment
deployment = client.create({
    "ipfs_definition_hash": ipfs_hash,
    # ... other fields
})
```

### Vault Funding

Deployments require funded vaults to run:

```python
# After creating deployment
print(f"Vault address: {deployment.vault}")
print(f"Fund at: https://solscan.io/account/{deployment.vault}")

# Check balance
balance = deployment.updateVaultBalance()
sol_balance = balance['SOL'] / 1e9  # Convert lamports to SOL
nos_balance = balance['NOS'] / 1e6  # Convert to NOS

print(f"Balance: {sol_balance:.6f} SOL, {nos_balance:.6f} NOS")
```

### Vault Withdrawal

Withdraw all funds from a vault back to your wallet:

```python
# Get vault object
vault = deployment.getVault()

# Withdraw all SOL and NOS tokens
try:
    signature = await vault.withdraw()
    print(f"Withdrawal successful: {signature}")
except Exception as e:
    print(f"Withdrawal failed: {e}")
```

**Important Notes:**
- Withdrawal uses the deployment-manager API to create withdrawal transactions
- The vault must contain **both SOL and NOS** tokens to withdraw successfully  
- Withdrawal returns all SOL and NOS tokens to your wallet
- Vaults with only SOL (no NOS) cannot withdraw due to missing NOS token accounts

**Troubleshooting Withdrawal Issues:**

If withdrawals fail with 500 server errors, this is because:
- The vault only has SOL but no NOS tokens
- The withdrawal handler tries to create NOS transactions but fails when there's no NOS token account
- **Solution**: Add some NOS tokens to the vault first, then withdraw
- Alternative: Wait for deployment-manager to support SOL-only withdrawals

The Python SDK detects this issue and provides clear guidance on the fix.

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
| `deployment.stop()` | `deployment.stop()` |
| `deployment.updateReplicaCount()` | `deployment.updateReplicaCount()` |
| `deployment.updateTimeout()` | `deployment.updateTimeout()` |
| `IPFS.pin()` | `upload_job_to_ipfs()` |

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