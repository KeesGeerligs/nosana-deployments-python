"""Vault functionality for Nosana Deployments SDK."""

from typing import Dict, Optional
import requests
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.system_program import transfer, TransferParams
from solders.hash import Hash
from solders.message import Message
import base64


class Vault:
    """Vault class matching TypeScript SDK interface exactly."""
    
    def __init__(self, public_key: str, wallet: Keypair, client):
        """Initialize vault.
        
        Args:
            public_key: Vault public key string
            wallet: User wallet keypair
            client: DeploymentsClient instance
        """
        self.public_key = public_key
        self.wallet = wallet
        self.client = client
    
    async def get_balance(self) -> Dict[str, float]:
        """Get vault balance in SOL and NOS.
        
        Returns:
            Dictionary with SOL and NOS balances
        """
        try:
            return self.client.update_vault_balance(self.public_key)
        except Exception as e:
            # Fallback to direct blockchain query
            return await self._get_balance_direct()
    
    async def _get_balance_direct(self) -> Dict[str, float]:
        """Get balance directly from Solana RPC."""
        rpc_url = "https://api.mainnet-beta.solana.com"
        
        try:
            # Get SOL balance
            sol_response = requests.post(rpc_url, json={
                "jsonrpc": "2.0",
                "id": 1, 
                "method": "getBalance",
                "params": [self.public_key]
            })
            
            sol_lamports = 0
            if sol_response.status_code == 200:
                result = sol_response.json()
                if "result" in result:
                    sol_lamports = result["result"]["value"]
            
            # Get NOS token balance using proper ATA calculation
            nos_balance = await self._get_nos_token_balance(rpc_url)
            
            return {
                "SOL": sol_lamports,
                "NOS": nos_balance
            }
            
        except Exception as e:
            return {"SOL": 0, "NOS": 0}
    
    async def _get_nos_token_balance(self, rpc_url: str) -> float:
        """Get NOS token balance from Associated Token Account.
        
        Matches the TypeScript SDK's getNosTokenAddressForAccount implementation.
        """
        try:
            # NOS token mint address (mainnet)
            NOS_MINT = "nosXBVoaCTtYdLvKY6Csb4AC8JCdQKKAaWYtx2ZMoo7"
            
            # Calculate Associated Token Account (ATA) address
            # This matches TypeScript SDK's getAssociatedTokenAddressSync()
            ata_address = self._calculate_ata_address(self.public_key, NOS_MINT)
            
            # Query token account balance
            token_response = requests.post(rpc_url, json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenAccountBalance", 
                "params": [ata_address]
            })
            
            if token_response.status_code == 200:
                result = token_response.json()
                if "result" in result and "value" in result["result"]:
                    # Get raw atomic balance and convert to human-readable (6 decimals)
                    atomic_balance = int(result["result"]["value"]["amount"])
                    return atomic_balance / 1e6  # Convert from atomic units
                
            return 0.0  # Token account doesn't exist or has no balance
            
        except Exception as e:
            print(f"   Debug: NOS balance error: {e}")
            return 0.0
    
    def _calculate_ata_address(self, wallet_address: str, mint_address: str) -> str:
        """Calculate Associated Token Account address.
        
        This is a simplified implementation. For production, you should use
        the proper SPL Token library or solders ATA calculation.
        """
        try:
            from solders.pubkey import Pubkey
            import hashlib
            
            # Token Program ID and Associated Token Program ID (standard Solana addresses)
            TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
            ASSOCIATED_TOKEN_PROGRAM_ID = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
            
            # Convert to Pubkey objects
            wallet_pubkey = Pubkey.from_string(wallet_address)
            mint_pubkey = Pubkey.from_string(mint_address)
            token_program_pubkey = Pubkey.from_string(TOKEN_PROGRAM_ID)
            assoc_token_program_pubkey = Pubkey.from_string(ASSOCIATED_TOKEN_PROGRAM_ID)
            
            # Find PDA (Program Derived Address) for ATA
            # This matches Solana's getAssociatedTokenAddressSync logic
            seeds = [
                bytes(wallet_pubkey),
                bytes(token_program_pubkey), 
                bytes(mint_pubkey)
            ]
            
            # Use solders to find the PDA
            ata_pubkey, _ = Pubkey.find_program_address(seeds, assoc_token_program_pubkey)
            
            return str(ata_pubkey)
            
        except Exception as e:
            print(f"   Debug: ATA calculation error: {e}")
            # Fallback - return empty string to indicate calculation failed
            return ""
    
    async def topup(self, sol: float = 0.0, nos: float = 0.0, lamports: bool = False) -> str:
        """Topup vault with SOL and/or NOS.
        
        Args:
            sol: Amount of SOL to transfer
            nos: Amount of NOS to transfer  
            lamports: If True, amounts are in lamports/raw units
            
        Returns:
            Transaction signature
        """
        if sol <= 0 and nos <= 0:
            raise ValueError("Must specify positive amount for SOL or NOS")
        
        signature = None
        if sol > 0:
            signature = await self._transfer_sol(sol, lamports)
        
        if nos > 0:
            raise NotImplementedError("NOS transfer not yet implemented")
            
        return signature
    
    async def _transfer_sol(self, amount: float, lamports: bool = False) -> str:
        """Transfer SOL from user wallet to vault using proper Solana transaction building.
        
        Matches the TypeScript SDK implementation exactly.
        
        Args:
            amount: SOL amount to transfer
            lamports: If True, amount is in lamports
            
        Returns:
            Transaction signature
        """
        try:
            # Convert to lamports if needed
            lamport_amount = int(amount) if lamports else int(amount * 1_000_000_000)
            
            # Create public keys
            from_pubkey = Pubkey.from_string(str(self.wallet.pubkey()))
            to_pubkey = Pubkey.from_string(self.public_key)
            
            # RPC connection
            rpc_url = "https://api.mainnet-beta.solana.com"
            
            # Check balance first (like TypeScript SDK)
            balance_response = requests.post(rpc_url, json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [str(from_pubkey)]
            })
            
            if balance_response.status_code == 200:
                balance_result = balance_response.json()
                if "result" in balance_result:
                    wallet_balance = balance_result["result"]["value"]
                    if wallet_balance < lamport_amount:
                        raise Exception(f"Insufficient SOL balance. Have {wallet_balance/1e9:.6f} SOL, need {lamport_amount/1e9:.6f} SOL")
            
            # Get recent blockhash
            blockhash_response = requests.post(rpc_url, json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getLatestBlockhash",
                "params": [{"commitment": "finalized"}]
            })
            
            if blockhash_response.status_code != 200:
                raise Exception(f"Failed to get blockhash: {blockhash_response.status_code}")
            
            blockhash_result = blockhash_response.json()
            if "error" in blockhash_result:
                raise Exception(f"RPC error: {blockhash_result['error']}")
            
            recent_blockhash = blockhash_result["result"]["value"]["blockhash"]
            
            # Create transfer instruction (matches TypeScript SystemProgram.transfer)
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=from_pubkey,
                    to_pubkey=to_pubkey,
                    lamports=lamport_amount
                )
            )
            
            # Build transaction the correct way for solders library
            # Create message with instruction and recent blockhash
            message = Message.new_with_blockhash([transfer_ix], from_pubkey, Hash.from_string(recent_blockhash))
            
            # Create transaction from message
            transaction = Transaction.new_unsigned(message)
            
            # Sign transaction (matches TypeScript transaction.sign)
            transaction.sign([self.wallet], Hash.from_string(recent_blockhash))
            
            # Serialize transaction using solders library __bytes__ method
            serialized_tx = bytes(transaction)
            
            # Send transaction using base64 encoding (like TypeScript)
            encoded_tx = base64.b64encode(serialized_tx).decode('ascii')
            
            send_response = requests.post(rpc_url, json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "sendTransaction",
                "params": [
                    encoded_tx,
                    {
                        "encoding": "base64",
                        "skipPreflight": False,
                        "preflightCommitment": "processed"
                    }
                ]
            })
            
            if send_response.status_code != 200:
                raise Exception(f"Failed to send transaction: {send_response.status_code}")
            
            send_result = send_response.json()
            if "error" in send_result:
                error_msg = send_result['error'].get('message', 'Unknown error')
                raise Exception(f"Transaction failed: {error_msg}")
            
            signature = send_result["result"]
            
            print(f"✅ SOL transfer successful!")
            print(f"   Amount: {amount} SOL ({lamport_amount:,} lamports)")
            print(f"   From: {from_pubkey}")  
            print(f"   To: {to_pubkey}")
            print(f"   Signature: {signature}")
            print(f"   View: https://solscan.io/tx/{signature}")
            
            return signature
            
        except Exception as e:
            raise Exception(f"SOL transfer failed: {e}")
    
    async def withdraw(self) -> None:
        """Withdraw all tokens from the vault.
        
        Uses the deployment manager API to create withdrawal transaction.
        """
        try:
            # Use the deployment manager withdraw endpoint
            response = self.client._request("POST", f"/api/vault/{self.public_key}/withdraw", json={
                "SOL": None,  # Withdraw all SOL
                "NOS": None   # Withdraw all NOS  
            })
            
            transaction_b64 = response.get("transaction")
            if not transaction_b64:
                raise Exception("No transaction returned from withdraw API")
            
            # TODO: Deserialize, sign, and send the transaction
            # This requires more complex transaction handling
            
            raise NotImplementedError(
                "Withdraw functionality requires transaction deserialization and signing. "
                "Use the Nosana dashboard to withdraw for now."
            )
            
        except Exception as e:
            raise Exception(f"Withdraw failed: {e}")


def create_vault(public_key: str, wallet: Keypair, client) -> Vault:
    """Create a vault instance.
    
    Args:
        public_key: Vault public key string
        wallet: User wallet keypair
        client: DeploymentsClient instance
        
    Returns:
        Vault instance
    """
    return Vault(public_key, wallet, client)