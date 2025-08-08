#!/usr/bin/env python3
"""
Fund all vaults with 0.1 NOS tokens using SPL token transfers.

This script sends NOS tokens directly to vault addresses via Solana RPC.
"""

import asyncio
import os
import requests
import base64
from nosana_deployments import create_nosana_deployment_client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.instruction import Instruction, AccountMeta
from solders.compute_budget import set_compute_unit_price

# NOS token mint address (mainnet)
NOS_MINT = Pubkey.from_string("nosXBVoaCTtYdLvKY6Csb4AC8JCdQKKAaWYtx2ZMoo7")
SPL_TOKEN_PROGRAM = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")

async def fund_vaults_with_nos():
    """Fund all vaults with SOL with 0.1 NOS tokens."""
    try:
        # Get private key from environment
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        if not private_key:
            print("❌ Set WALLET_PRIVATE_KEY environment variable")
            return

        print("🏦 Funding vaults with NOS tokens")
        print("=" * 40)
        
        # Create client
        client = create_nosana_deployment_client(
            manager="https://deployment-manager.k8s.prd.nos.ci",
            key=private_key
        )
        
        # Create keypair from private key
        wallet = Keypair.from_base58_string(private_key)
        
        print(f"✅ Client created")
        print(f"🔑 Wallet: {wallet.pubkey()}")
        
        # Get all vaults
        print("\n📋 Getting vaults...")
        vaults = client.get_vaults()
        print(f"   Found {len(vaults)} vault(s)")
        
        # Filter vaults that have SOL but need NOS
        vaults_to_fund = []
        for i, vault_data in enumerate(vaults, 1):
            vault_id = vault_data.get("vault")
            sol_balance = vault_data.get("sol", 0) / 1e9  # Convert lamports to SOL
            nos_balance = vault_data.get("nos", 0) / 1e6  # Convert to NOS
            
            print(f"🏦 Vault {i}: {vault_id}")
            print(f"   Balance: {sol_balance:.6f} SOL, {nos_balance:.6f} NOS")
            
            if sol_balance > 0.001 and nos_balance < 0.01:  # Has SOL but no/little NOS
                vaults_to_fund.append(vault_id)
                print(f"   ✅ Will fund with 0.1 NOS")
            else:
                print(f"   ⏭️  Skipping - already has NOS or no SOL")
        
        if not vaults_to_fund:
            print("\n✨ No vaults need NOS funding")
            return
        
        print(f"\n💰 Funding {len(vaults_to_fund)} vaults with 0.1 NOS each...")
        nos_amount = int(0.1 * 1e6)  # 0.1 NOS in smallest units
        
        # Get source token account (where we're sending NOS from)
        source_token_account = await get_associated_token_account(wallet.pubkey(), NOS_MINT)
        print(f"📍 Source NOS account: {source_token_account}")
        
        # Check NOS balance
        nos_balance = await get_token_balance(source_token_account)
        total_needed = len(vaults_to_fund) * nos_amount
        print(f"💰 Available NOS: {nos_balance/1e6:.6f}")
        print(f"💰 Total needed: {total_needed/1e6:.6f}")
        
        if nos_balance < total_needed:
            print(f"❌ Insufficient NOS balance. Need {total_needed/1e6:.6f} NOS, have {nos_balance/1e6:.6f}")
            return
        
        # Send NOS to each vault
        successful_transfers = 0
        for vault_id in vaults_to_fund:
            try:
                print(f"\n🔄 Funding vault {vault_id}...")
                
                # Get destination token account
                vault_pubkey = Pubkey.from_string(vault_id)
                dest_token_account = await get_associated_token_account(vault_pubkey, NOS_MINT)
                
                # Create transaction
                tx_signature = await send_nos_tokens(
                    wallet,
                    source_token_account, 
                    dest_token_account,
                    vault_pubkey,
                    nos_amount
                )
                
                if tx_signature:
                    print(f"   ✅ Success: {tx_signature}")
                    successful_transfers += 1
                else:
                    print(f"   ❌ Failed to send NOS")
                    
            except Exception as e:
                print(f"   ❌ Error funding vault {vault_id}: {e}")
        
        print(f"\n🎉 Successfully funded {successful_transfers}/{len(vaults_to_fund)} vaults")
        print(f"💡 Now run: python withdraw_funds.py")
        
    except Exception as e:
        print(f"❌ Funding failed: {e}")
        import traceback
        traceback.print_exc()

async def get_associated_token_account(owner: Pubkey, mint: Pubkey) -> Pubkey:
    """Get associated token account address."""
    # This is a simplified version - in practice you'd use the proper ATA derivation
    ASSOCIATED_TOKEN_PROGRAM = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    
    seeds = [
        bytes(owner),
        bytes(SPL_TOKEN_PROGRAM), 
        bytes(mint)
    ]
    
    # Find PDA for associated token account
    ata_address, _ = Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM)
    return ata_address

async def get_token_balance(token_account: Pubkey) -> int:
    """Get token account balance via RPC."""
    try:
        rpc_url = "https://api.mainnet-beta.solana.com"
        response = requests.post(rpc_url, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountBalance",
            "params": [str(token_account)]
        })
        
        if response.status_code == 200:
            result = response.json()
            if "result" in result and result["result"]["value"]:
                return int(result["result"]["value"]["amount"])
        return 0
    except:
        return 0

async def send_nos_tokens(wallet: Keypair, source: Pubkey, dest: Pubkey, dest_owner: Pubkey, amount: int) -> str:
    """Send NOS tokens using SPL token transfer."""
    try:
        # Create transfer instruction
        transfer_instruction = create_transfer_instruction(
            source=source,
            destination=dest,
            owner=wallet.pubkey(),
            amount=amount
        )
        
        # Get recent blockhash
        rpc_url = "https://api.mainnet-beta.solana.com"
        blockhash_response = requests.post(rpc_url, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getLatestBlockhash"
        })
        
        if blockhash_response.status_code != 200:
            return None
            
        blockhash = blockhash_response.json()["result"]["value"]["blockhash"]
        
        # Build transaction
        message = MessageV0.try_compile(
            payer=wallet.pubkey(),
            instructions=[transfer_instruction],
            address_lookup_tables=[],
            recent_blockhash=blockhash
        )
        
        tx = VersionedTransaction(message, [wallet])
        
        # Send transaction
        tx_bytes = bytes(tx)
        encoded_tx = base64.b64encode(tx_bytes).decode()
        
        send_response = requests.post(rpc_url, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [encoded_tx, {"encoding": "base64"}]
        })
        
        if send_response.status_code == 200:
            result = send_response.json()
            if "result" in result:
                return result["result"]
        
        return None
        
    except Exception as e:
        print(f"Error in send_nos_tokens: {e}")
        return None

def create_transfer_instruction(source: Pubkey, destination: Pubkey, owner: Pubkey, amount: int) -> Instruction:
    """Create SPL token transfer instruction."""
    # SPL Token Transfer instruction
    # Instruction: 3 (Transfer)
    data = bytes([3]) + amount.to_bytes(8, 'little')
    
    return Instruction(
        program_id=SPL_TOKEN_PROGRAM,
        accounts=[
            AccountMeta(pubkey=source, is_signer=False, is_writable=True),
            AccountMeta(pubkey=destination, is_signer=False, is_writable=True),
            AccountMeta(pubkey=owner, is_signer=True, is_writable=False),
        ],
        data=data
    )

if __name__ == "__main__":
    asyncio.run(fund_vaults_with_nos())