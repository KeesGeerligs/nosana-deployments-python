#!/usr/bin/env python3
"""
Withdraw all funds from Nosana vault deployments.

This script finds all vaults with funds and attempts to withdraw them back to your wallet.
Set WALLET_PRIVATE_KEY environment variable with your wallet private key.
"""

import asyncio
import os
from nosana_deployments import create_nosana_deployment_client

async def withdraw_all_funds():
    """Withdraw all funds from vault deployments."""
    try:
        # Get private key from environment
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        if not private_key:
            print("❌ Set WALLET_PRIVATE_KEY environment variable")
            return
        
        print("🔑 Creating client...")
        client = create_nosana_deployment_client(
            manager="https://deployment-manager.k8s.prd.nos.ci",
            key=private_key
        )
        
        print(f"✅ Client created")
        print(f"🔑 Wallet: {client.auth.user_id}")
        
        # Get all vaults
        print("\n📋 Getting vaults...")
        try:
            vaults = client.get_vaults()
            print(f"   Found {len(vaults)} vault(s)")
            
            if not vaults:
                print("❌ No vaults found")
                return
                
        except Exception as vault_list_error:
            print(f"❌ Failed to get vaults: {vault_list_error}")
            
            # Check if it's an authentication error
            if "401" in str(vault_list_error) or "unauthorized" in str(vault_list_error).lower():
                print("   🔍 This is an authentication error - the nacl signature fix may not be working")
            elif "404" in str(vault_list_error):
                print("   🔍 Vaults endpoint not found - may need different API endpoint")
            elif "500" in str(vault_list_error):
                print("   🔍 Server error - authentication may be working but server has issues")
                
            return
        
        # Test each vault for balances and attempt withdrawal
        for i, vault_data in enumerate(vaults):
            vault_address = vault_data.get("address") or vault_data.get("vault") or vault_data.get("id")
            print(f"\n🏦 Vault {i+1}: {vault_address}")
            
            # Get vault instance
            vault = client.get_vault(vault_address)
            
            # Get balance
            print("   💰 Checking balance...")
            try:
                balance = await vault.get_balance()
                sol_balance = balance.get("SOL", 0) / 1e9  # Convert from lamports
                nos_balance = balance.get("NOS", 0)
                
                print(f"      SOL: {sol_balance:.6f}")
                print(f"      NOS: {nos_balance:.6f}")
                
                # Only attempt withdrawal if there's a meaningful balance
                if sol_balance > 0.0001 or nos_balance > 0.0001:
                    print("   🏃 Attempting withdrawal...")
                    
                    # Test withdrawal
                    try:
                        signature = await vault.withdraw()
                        print(f"   ✅ Withdrawal successful!")
                        print(f"      Signature: {signature}")
                        print(f"      View: https://solscan.io/tx/{signature}")
                        
                    except Exception as withdraw_error:
                        print(f"   ❌ Withdrawal failed: {withdraw_error}")
                        
                        # Check if it's an authentication error
                        if "401" in str(withdraw_error) or "unauthorized" in str(withdraw_error).lower():
                            print("   🔍 Authentication error - nacl signature may still have issues")
                        elif "404" in str(withdraw_error):
                            print("   🔍 Withdrawal endpoint not found")
                        elif "500" in str(withdraw_error):
                            print("   🔍 Server error - authentication may be working but server has issues")
                        elif "insufficient" in str(withdraw_error).lower():
                            print("   🔍 Insufficient balance or funds error")
                        
                else:
                    print("   ⏭️  Skipping - balance too low")
                    
            except Exception as balance_error:
                print(f"   ❌ Balance check failed: {balance_error}")
        
    except Exception as e:
        print(f"❌ Withdrawal failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(withdraw_all_funds())