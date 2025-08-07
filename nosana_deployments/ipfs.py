"""IPFS upload functionality for Nosana Deployments SDK."""

import json
import requests
from typing import Dict, Any, Optional


class IPFSClient:
    """IPFS client using Pinata Cloud like the TypeScript SDK."""
    
    def __init__(self, environment: str = "mainnet", jwt: Optional[str] = None):
        """Initialize IPFS client.
        
        Args:
            environment: 'mainnet' or 'devnet'
            jwt: Optional custom JWT token
        """
        self.environment = environment
        
        # Use the same Pinata configuration as TypeScript SDK
        self.config = {
            "mainnet": {
                "api": "https://api.pinata.cloud",
                "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiJmZDUwODE1NS1jZDJhLTRlMzYtYWI4MC0wNmMxNjRmZWY1MTkiLCJlbWFpbCI6Implc3NlQG5vc2FuYS5pbyIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJwaW5fcG9saWN5Ijp7InJlZ2lvbnMiOlt7ImlkIjoiRlJBMSIsImRlc2lyZWRSZXBsaWNhdGlvbkNvdW50IjoxfV0sInZlcnNpb24iOjF9LCJtZmFfZW5hYmxlZCI6ZmFsc2UsInN0YXR1cyI6IkFDVElWRSJ9LCJhdXRoZW50aWNhdGlvblR5cGUiOiJzY29wZWRLZXkiLCJzY29wZWRLZXlLZXkiOiI1YzVhNWM2N2RlYWU2YzNhNzEwOCIsInNjb3BlZEtleVNlY3JldCI6ImYxOWFjZDUyZDk4ZTczNjU5MmEyY2IzZjQwYWUxNGE2ZmYyYTkxNDJjZTRiN2EzZGQ5OTYyOTliMmJkN2IzYzEiLCJpYXQiOjE2ODY3NzE5Nzl9.r4_pWCCT79Jis6L3eegjdBdAt5MpVd1ymDkBuNE25g8",
                "gateway": "https://nosana.mypinata.cloud/ipfs/"
            },
            "devnet": {
                "api": "https://api.pinata.cloud", 
                "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiJmZDUwODE1NS1jZDJhLTRlMzYtYWI4MC0wNmMxNjRmZWY1MTkiLCJlbWFpbCI6Implc3NlQG5vc2FuYS5pbyIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJwaW5fcG9saWN5Ijp7InJlZ2lvbnMiOlt7ImlkIjoiRlJBMSIsImRlc2lyZWRSZXBsaWNhdGlvbkNvdW50IjoxfV0sInZlcnNpb24iOjF9LCJtZmFfZW5hYmxlZCI6ZmFsc2UsInN0YXR1cyI6IkFDVElWRSJ9LCJhdXRoZW50aWNhdGlvblR5cGUiOiJzY29wZWRLZXkiLCJzY29wZWRLZXlLZXkiOiI1YzVhNWM2N2RlYWU2YzNhNzEwOCIsInNjb3BlZEtleVNlY3JldCI6ImYxOWFjZDUyZDk4ZTczNjU5MmEyY2IzZjQwYWUxNGE2ZmYyYTkxNDJjZTRiN2EzZGQ5OTYyOTliMmJkN2IzYzEiLCJpYXQiOjE2ODY3NzE5Nzl9.r4_pWCCT79Jis6L3eegjdBdAt5MpVd1ymDkBuNE25g8",
                "gateway": "https://nosana.mypinata.cloud/ipfs/"
            }
        }
        
        # Use custom JWT or environment default
        self.jwt = jwt or self.config[environment]["jwt"]
        self.api_url = self.config[environment]["api"]
        self.gateway = self.config[environment]["gateway"]
    
    def pin(self, data: Dict[str, Any]) -> str:
        """Pin JSON data to IPFS using Pinata (matches TypeScript SDK).
        
        Args:
            data: JSON data to pin
            
        Returns:
            IPFS hash
            
        Raises:
            Exception: If upload fails
        """
        try:
            # Match the TypeScript SDK implementation exactly
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt}"
            }
            
            response = requests.post(
                f"{self.api_url}/pinning/pinJSONToIPFS",
                json=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["IpfsHash"]
            else:
                raise Exception(f"Pinata upload failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"IPFS upload failed: {e}")


def upload_job_to_ipfs(job_definition: Dict[str, Any], environment: str = "mainnet") -> str:
    """Upload job definition to IPFS using Pinata (matches TypeScript SDK).
    
    Args:
        job_definition: Job definition dictionary
        environment: 'mainnet' or 'devnet'
        
    Returns:
        IPFS hash
    """
    client = IPFSClient(environment=environment)
    return client.pin(job_definition)