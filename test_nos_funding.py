#!/usr/bin/env python3
"""
Test NOS funding functionality by sending 0.1 NOS to all vaults with SOL.
"""

import asyncio
import os
from nosana_deployments import create_nosana_deployment_client

async def test_nos_funding():
    """Test funding vaults with NOS using the vault.topup() method."""
    try:
        # Get private key from environment
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        if not private_key:
            print("❌ Set WALLET_PRIVATE_KEY environment variable")
            return

        print("🧪 Testing NOS funding functionality")
        print("=" * 40)
        
        # Create client
        client = create_nosana_deployment_client(
            manager="https://deployment-manager.k8s.prd.nos.ci",
            key=private_key
        )
        
        print(f"✅ Client created")
        print(f"🔑 Wallet: {client.auth.user_id}")
        
        # Get all vaults
        print("\n📋 Getting vaults...")
        vaults = client.get_vaults()
        print(f"   Found {len(vaults)} vault(s)")
        
        # Find vaults that need NOS
        vaults_to_fund = []
        for i, vault_data in enumerate(vaults, 1):
            vault_id = vault_data.get("vault")
            sol_balance = vault_data.get("sol", 0) / 1e9  # Convert lamports to SOL
            nos_balance = vault_data.get("nos", 0) / 1e6  # Convert to NOS
            
            print(f"🏦 Vault {i}: {vault_id}")
            print(f"   Balance: {sol_balance:.6f} SOL, {nos_balance:.6f} NOS")
            
            if sol_balance > 0.001 and nos_balance < 0.01:  # Has SOL but little/no NOS
                vaults_to_fund.append(vault_id)
                print(f"   ✅ Needs NOS funding")
            else:
                print(f"   ⏭️  Skipping - already has NOS or no SOL")
        
        if not vaults_to_fund:
            print("\n✨ No vaults need NOS funding")
            return
        
        print(f"\n💰 Will fund {len(vaults_to_fund)} vaults with 0.1 NOS each...")
        
        # Fund each vault
        successful_funds = 0
        for vault_id in vaults_to_fund:
            try:
                print(f"\n🔄 Funding vault: {vault_id}")
                
                # Get vault instance
                vault = client.get_vault(vault_id)
                
                # Topup with 0.1 NOS
                signature = await vault.topup(nos=0.1)
                
                if signature:
                    print(f"   ✅ Success! Signature: {signature}")
                    successful_funds += 1
                else:
                    print(f"   ❌ Failed - no signature returned")
                    
            except Exception as e:
                print(f"   ❌ Error funding {vault_id}: {e}")
        
        print(f"\n🎉 Successfully funded {successful_funds}/{len(vaults_to_fund)} vaults")
        
        if successful_funds > 0:
            print(f"💡 Now you can run: python withdraw_funds.py")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_nos_funding())