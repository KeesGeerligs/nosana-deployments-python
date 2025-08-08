# Nosana Deployments Python SDK

Simple Python SDK for the Nosana Deployment Manager API. Matches the TypeScript SDK interface for a consistent developer experience.

## 🚀 Quick Start

1) Configure your wallet key (base58 or hex) in a `.env` file at the project root:

```
WALLET_PRIVATE_KEY=your_base58_or_hex_key
# Optional: enable verbose HTTP diagnostics
# NOSANA_SDK_DEBUG=1
```

2) Create a virtual environment and install dependencies:

```
python -m venv venv
source venv/bin/activate
pip install -e .
```

3) Make sure your wallet has at least 0.02 SOL and 3+ NOS to pass preflight checks.

## 🎯 Scripts

### Create and Run a Deployment

Creates a deployment for the provided PyTorch Jupyter job, funds its vault with 0.01 SOL and 3 NOS, and starts the job (1 hour timeout). The script performs preflight balance checks and retries start once if needed.

```
python deploy_and_run.py
```

Outputs:
- IPFS hash
- Deployment ID and vault address
- SOL and NOS funding transaction signatures
- Start request confirmation

### Stop and Withdraw

You can stop via the dashboard or programmatically. Then withdraw funds back to your wallet:

```
python withdraw_funds.py
```

Notes:
- The withdrawal script scans your deployments for vaults and withdraws balances using a server-generated transaction that you co-sign locally.
- Vaults must have both SOL and NOS token accounts for withdrawal to succeed.
- Set `NOSANA_SDK_DEBUG=1` if you need to see HTTP request diagnostics.

## 📦 Programmatic Usage

```python
from nosana_deployments import create_nosana_deployment_client, upload_job_to_ipfs

client = create_nosana_deployment_client(
    manager="https://deployment-manager.k8s.prd.nos.ci",
    key="WALLET_PRIVATE_KEY",
)

job_def = {"ops": [...], "type": "container", "version": "0.1"}
ipfs_hash = upload_job_to_ipfs(job_def)

deployment = client.create({
    "name": "My Job",
    "market": "97G9NnvBDQ2WpKu6fasoMsAKmfj63C9rhysJnkeWodAf",
    "ipfs_definition_hash": ipfs_hash,
    "strategy": "SIMPLE",
    "replicas": 1,
    "timeout": 3600,
})

vault = client.get_vault(deployment.vault)
# await vault.topup(sol=0.01)
# await vault.topup(nos=3.0)

deployment.start()
```

## 🔧 Development

- Python 3.9+
- Dependencies are defined in `pyproject.toml`.
- Environment variables can be provided via `.env` (loaded by the scripts).