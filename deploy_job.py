#!/usr/bin/env python3
"""
Deploy and test a Nosana job using the Python SDK.

This script demonstrates the complete workflow: create deployment, fund vault, start job.
Set WALLET_PRIVATE_KEY environment variable with your wallet private key.
"""

import os
from nosana_deployments import create_nosana_deployment_client, upload_job_to_ipfs

def main():
    """Deploy a test job to Nosana network."""
    
    print("🚀 Nosana Job Deployment Test")
    print("=" * 40)
    
    # 1. Create client
    private_key = os.getenv("WALLET_PRIVATE_KEY")
    if not private_key:
        print("❌ Set WALLET_PRIVATE_KEY environment variable")
        return None
    
    client = create_nosana_deployment_client(
        manager="https://deployment-manager.k8s.prd.nos.ci",
        key=private_key
    )
    print(f"✅ Client created for wallet: {client.auth.user_id}")
    
    # 2. Define job
    job_definition = {
        "ops": [
            {
                "id": "pytorch-jupyter",
                "type": "container/run",
                "args": {
                    "image": "docker.io/nosana/pytorch-jupyter:2.0.0",
                    "cmd": ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser"],
                    "gpu": True,
                    "expose": 8888
                }
            }
        ],
        "type": "container",
        "version": "0.1"
    }
    
    # 3. Upload to IPFS
    print("📤 Uploading job to IPFS...")
    ipfs_hash = upload_job_to_ipfs(job_definition)
    print(f"✅ IPFS hash: {ipfs_hash}")
    
    # 4. Create deployment
    deployment_config = {
        "name": "Python SDK Test - PyTorch Jupyter",
        "market": "97G9NnvBDQ2WpKu6fasoMsAKmfj63C9rhysJnkeWodAf",
        "ipfs_definition_hash": ipfs_hash,
        "strategy": "SIMPLE", 
        "replicas": 1,
        "timeout": 3600  # 1 hour
    }
    
    print("🏗️  Creating deployment...")
    deployment = client.create(deployment_config)
    print(f"✅ Deployment created: {deployment.id}")
    print(f"   Name: {deployment.name}")
    print(f"   Status: {deployment.status}")
    print(f"   Vault: {deployment.vault}")
    
    # 5. Check vault balance
    print("\n💰 Checking vault balance...")
    try:
        balance = deployment.updateVaultBalance()
        sol_balance = balance['SOL'] / 1e9
        nos_balance = balance['NOS'] / 1e6
        print(f"   Balance: {sol_balance:.6f} SOL, {nos_balance:.6f} NOS")
        
        if sol_balance > 0.01 or nos_balance > 10:  # Minimum needed for job
            print("   ✅ Vault has sufficient funds")
            
            # 6. Start deployment
            print("\n🚀 Starting deployment...")
            try:
                deployment.start()
                print("✅ Deployment started successfully!")
                print("   Check status at: https://nosana.io/dashboard")
            except Exception as e:
                print(f"❌ Start failed: {e}")
        else:
            print("   ❌ Insufficient funds")
            print(f"\n⚠️  Fund the vault to start deployment:")
            print(f"   Address: {deployment.vault}")
            print(f"   Amount needed: ~0.02 SOL or 50 NOS")
            print(f"   Fund at: https://solscan.io/account/{deployment.vault}")
            
    except Exception as e:
        print(f"❌ Balance check failed: {e}")
    
    # 7. Show summary
    print(f"\n📊 Deployment Summary:")
    print(f"   ID: {deployment.id}")
    print(f"   Vault: {deployment.vault}")
    print(f"   Market: {deployment.market}")
    print(f"   Status: {deployment.status}")
    
    return deployment

if __name__ == "__main__":
    main()