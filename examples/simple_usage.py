#!/usr/bin/env python3
"""
Simple usage example for Nosana Deployments Python SDK.

This example shows basic SDK usage without the full workflow.
For a complete deployment example, see ../deploy_job.py
"""

import os
from nosana_deployments import create_nosana_deployment_client, upload_job_to_ipfs

def main():
    """Simple deployment example."""
    
    print("🔧 Simple Nosana Deployments SDK Usage")
    print("=" * 50)
    
    # 1. Create client
    client = create_nosana_deployment_client(
        manager="https://deployment-manager.k8s.prd.nos.ci",
        key=os.getenv("WALLET_PRIVATE_KEY", "your_private_key_here")  # Your wallet private key
    )
    print(f"✅ Client created for wallet: {client.auth.user_id}")
    
    # 2. Simple job definition
    job_definition = {
        "ops": [
            {
                "id": "hello-world",
                "type": "container/run",
                "args": {
                    "image": "hello-world:latest",
                    "cmd": ["echo", "Hello Nosana!"]
                }
            }
        ],
        "type": "container",
        "version": "0.1"
    }
    
    # 3. Upload to IPFS
    ipfs_hash = upload_job_to_ipfs(job_definition)
    print(f"✅ Job uploaded to IPFS: {ipfs_hash}")
    
    # 4. Deployment configuration
    deployment_config = {
        "name": "Simple Hello World",
        "market": "97G9NnvBDQ2WpKu6fasoMsAKmfj63C9rhysJnkeWodAf",
        "ipfs_definition_hash": ipfs_hash,
        "strategy": "SIMPLE", 
        "replicas": 1,
        "timeout": 300  # 5 minutes
    }
    
    # 5. Create deployment
    deployment = client.create(deployment_config)
    print(f"✅ Created deployment: {deployment.id}")
    print(f"   Status: {deployment.status}")
    print(f"   Vault: {deployment.vault}")
    
    # 6. Fund vault (manual step)
    print(f"\n⚠️  Fund the vault before starting:")
    print(f"   Vault Address: {deployment.vault}")
    print(f"   Send SOL/NOS to this address")
    print(f"   https://solscan.io/account/{deployment.vault}")
    
    # 7. Check vault balance
    try:
        balance = deployment.updateVaultBalance()
        sol_balance = balance['SOL'] / 1e9  # Convert lamports to SOL
        nos_balance = balance['NOS'] / 1e6  # Convert to NOS
        print(f"   Current balance: {sol_balance:.6f} SOL, {nos_balance:.6f} NOS")
        
        if sol_balance > 0 or nos_balance > 0:
            print("   ✅ Vault has funds!")
        else:
            print("   ❌ Vault is empty")
            
    except Exception as e:
        print(f"   Could not check balance: {e}")
    
    # 8. Start deployment (if funded)
    try:
        deployment.start()
        print("🚀 Deployment started!")
    except Exception as e:
        print(f"⚠️  Start failed: {e}")
        print("   Fund the vault and try again")
    
    # 9. List all deployments
    deployments = client.list()
    print(f"\n📋 Found {len(deployments)} total deployments")
    
    # 10. Use pipe for chaining operations
    print("\n🔗 Pipe example:")
    try:
        client.pipe(
            deployment.id,  # Get existing deployment
            lambda d: print(f"   Pipeline processing: {d.name}"),
            lambda d: print(f"   Status: {d.status}"),
        )
        print("   Pipeline completed")
    except Exception as e:
        print(f"   Pipeline failed: {e}")
    
    # 11. Available deployment methods
    print(f"\n🛠️  Available methods on deployment object:")
    methods = [
        'start()', 'stop()', 'archive()',
        'getTasks()', 'updateReplicaCount(n)', 
        'updateTimeout(seconds)', 'updateVaultBalance()'
    ]
    for method in methods:
        print(f"   • deployment.{method}")
    
    print(f"\n✨ SDK usage example complete!")
    return deployment

if __name__ == "__main__":
    main()