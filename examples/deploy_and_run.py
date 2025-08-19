#!/usr/bin/env python3
"""
Create a deployment, fund its vault (0.01 SOL, 3 NOS), and start the job.

Reads WALLET_PRIVATE_KEY from environment or .env.
"""

import os
import asyncio
from dotenv import load_dotenv
from nosana_deployments import create_nosana_deployment_client, upload_job_to_ipfs
import requests

RPC_URL = "https://api.mainnet-beta.solana.com"


load_dotenv()


JOB_DEF = {
    "ops": [
        {
            "id": "Pytorch",
            "args": {
                "cmd": [
                    "jupyter",
                    "lab",
                    "--ip=0.0.0.0",
                    "--port=8888",
                    "--no-browser",
                    "--allow-root",
                    "--ServerApp.token=''",
                    "--ServerApp.password=''",
                ],
                "gpu": True,
                "image": "docker.io/nosana/pytorch-jupyter:2.0.0",
                "expose": 8888,
            },
            "type": "container/run",
        }
    ],
    "meta": {
        "trigger": "dashboard",
        "system_requirements": {"required_vram": 4},
    },
    "type": "container",
    "version": "0.1",
}


async def main() -> None:
    print("🚀 Create & Run Deployment")
    print("=" * 40)

    private_key = os.getenv("WALLET_PRIVATE_KEY")
    if not private_key:
        print("❌ Set WALLET_PRIVATE_KEY in environment or .env")
        return

    # Create client
    client = create_nosana_deployment_client(
        manager="https://deployment-manager.k8s.prd.nos.ci",
        key=private_key,
    )
    print(f"✅ Client created for wallet: {client.auth.user_id}")

    # Preflight: check wallet balances
    def get_sol(pk: str) -> int:
        r = requests.post(RPC_URL, json={"jsonrpc":"2.0","id":1,"method":"getBalance","params":[pk]})
        return r.json().get("result",{}).get("value",0) if r.status_code==200 else 0
    def get_nos_units(pk: str) -> int:
        # NOS mint
        mint = "nosXBVoaCTtYdLvKY6Csb4AC8JCdQKKAaWYtx2ZMoo7"
        token_prog = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
        ata_prog = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
        from solders.pubkey import Pubkey
        owner = Pubkey.from_string(client.auth.user_id)
        mint_pk = Pubkey.from_string(mint)
        token_prog_pk = Pubkey.from_string(token_prog)
        ata_prog_pk = Pubkey.from_string(ata_prog)
        ata,_ = Pubkey.find_program_address([bytes(owner), bytes(token_prog_pk), bytes(mint_pk)], ata_prog_pk)
        r = requests.post(RPC_URL, json={"jsonrpc":"2.0","id":1,"method":"getTokenAccountBalance","params":[str(ata)]})
        if r.status_code==200 and r.json().get("result",{}).get("value"):
            return int(r.json()["result"]["value"]["amount"]) 
        return 0
    sol_lamports = get_sol(client.auth.user_id)
    nos_units = get_nos_units(client.auth.user_id)
    if sol_lamports < 12_000_000 or nos_units < 3_000_000:
        need_sol = max(0, 12_000_000 - sol_lamports)/1e9
        need_nos = max(0, 3_000_000 - nos_units)/1e6
        print(f"⚠️  Low wallet balance. Top up before running:")
        if need_sol>0: print(f"   - Add at least {need_sol:.4f} SOL")
        if need_nos>0: print(f"   - Add at least {need_nos:.3f} NOS")
        return

    # Upload job def to IPFS
    print("📤 Uploading job definition to IPFS...")
    ipfs_hash = upload_job_to_ipfs(JOB_DEF)
    print(f"✅ IPFS hash: {ipfs_hash}")

    # Create deployment (1-hour timeout)
    deployment_config = {
        "name": "PyTorch Jupyter Lab",
        "market": "97G9NnvBDQ2WpKu6fasoMsAKmfj63C9rhysJnkeWodAf",
        "ipfs_definition_hash": ipfs_hash,
        "strategy": "SIMPLE",
        "replicas": 1,
        "timeout": 3600,
    }

    print("🏗️  Creating deployment...")
    deployment = client.create(deployment_config)
    print(f"✅ Deployment: {deployment.id}")
    print(f"   Vault: {deployment.vault}")

    # Fund the vault: 0.01 SOL + 3 NOS
    print("\n💰 Funding vault with 0.01 SOL and 3 NOS...")
    vault = client.get_vault(deployment.vault)
    try:
        sol_sig = await vault.topup(sol=0.01)
        print(f"   ✅ SOL tx: {sol_sig}")
        nos_sig = await vault.topup(nos=3.0)
        print(f"   ✅ NOS tx: {nos_sig}")
    except Exception as fund_err:
        print(f"❌ Funding failed: {fund_err}")
        return

    # Optional short wait for balance reflection
    await asyncio.sleep(5)

    # Start the deployment
    print("\n🚀 Starting deployment...")
    try:
        deployment.start()
        print("✅ Deployment start requested")
        print("🔗 Check status: https://nosana.io/dashboard")
    except Exception as start_err:
        print(f"⚠️  Start failed once: {start_err}")
        await asyncio.sleep(5)
        try:
            deployment.start()
            print("✅ Deployment start re-requested")
        except Exception as start_err2:
            print(f"❌ Start failed: {start_err2}")
            return

    # Summary
    print("\n📊 Summary")
    print(f"   Deployment: {deployment.id}")
    print(f"   Vault: {deployment.vault}")


if __name__ == "__main__":
    asyncio.run(main()) 