import json
import os
import time
from pinetree.client import PineTreeAgentClient

# 1. Dynamically load the ABI from the pinetree directory
abi_path = os.path.join(os.path.dirname(__file__), 'pinetree', 'abi.json')
with open(abi_path, 'r') as f:
    contract_abi = json.load(f)

# 2. Network Configuration
BASE_RPC = "https://base-mainnet.g.alchemy.com/v2/nlTBtp-FG45Dd-i8M2G6i"
CONTRACT_ADDRESS = "0x611515Ae224c06704013DB44be9BE61Fa378B31d"

def run_scanner_bot():
    print("[*] Initializing Pine Tree Agent Scanner...")
    
    client = PineTreeAgentClient(
        rpc_url=BASE_RPC,
        contract_address=CONTRACT_ADDRESS,
        abi=contract_abi
    )

    # Let's scan the first 5 markets of your Base Matrix series
    target_ids = [31000, 31001, 31002, 31003, 31004, 31005]
    live_matrix = []

    print(f"[*] Commencing rapid scan of {len(target_ids)} markets...")
    print("-" * 40)

    for m_id in target_ids:
        market_data = client.get_market(m_id)
        
        # If it's initialized, add it to our agent's memory bank
        if market_data.get("initialized") == True:
            print(f"[+] Market {m_id} is LIVE. YES Pool: {market_data['pool_yes']} | NO Pool: {market_data['pool_no']}")
            live_matrix.append(market_data)
        else:
            print(f"[-] Market {m_id} is unminted/inactive.")
            
        time.sleep(0.1) # Tiny sleep to respect Alchemy RPC rate limits

    print("-" * 40)
    print(f"[*] Scan complete. Found {len(live_matrix)} active tradeable pools.")
    
    # This live_matrix array is exactly what an AI model would ingest to find arbitrage!

if __name__ == "__main__":
    run_scanner_bot()
