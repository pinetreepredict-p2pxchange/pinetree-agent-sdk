import json
from web3 import Web3

class PineTreeAgentClient:
    """
    Official Python SDK for Pine Tree Predict ($PTP).
    Built for the Agentic Economy on Base Mainnet.
    """
    
    # Core Protocol Addresses (Base Mainnet)
    EXCHANGE_ADDRESS = "0x611515Ae224c06704013DB44be9BE61Fa378B31d"
    USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    KYA_REGISTRY_ADDRESS = "0xA3cEd55dDbfCF858f1BCD56B259d8B5b6e301cbc" # KYA VIP Lane
    
    # Minimal ABIs for agentic routing
    KYA_ABI = json.loads('''[
        {
            "inputs": [{"internalType": "address", "name": "_wallet", "type": "address"}],
            "name": "checkAgentStatus",
            "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]''')
    
    EXCHANGE_ABI = json.loads('''[
        {"inputs": [{"internalType": "uint256", "name": "_marketId", "type": "uint256"}, {"internalType": "bool", "name": "_isYes", "type": "bool"}, {"internalType": "uint256", "name": "_amount", "type": "uint256"}], "name": "placeBet", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
        {"inputs": [{"internalType": "uint256", "name": "_marketId", "type": "uint256"}], "name": "claimWinnings", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
        {"inputs": [{"internalType": "uint256", "name": "_marketId", "type": "uint256"}], "name": "getMarket", "outputs": [{"internalType": "bool", "name": "initialized", "type": "bool"}, {"internalType": "bool", "name": "resolved", "type": "bool"}, {"internalType": "bool", "name": "canceled", "type": "bool"}, {"internalType": "bool", "name": "result", "type": "bool"}, {"internalType": "uint256", "name": "yesPool", "type": "uint256"}, {"internalType": "uint256", "name": "noPool", "type": "uint256"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "stateMutability": "view", "type": "function"}
    ]''')

    USDC_ABI = json.loads('''[
        {"inputs": [{"internalType": "address", "name": "spender", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
        {"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
    ]''')

    def __init__(self, private_key: str, rpc_url: str = "https://mainnet.base.org"):
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.web3.is_connected():
            raise ConnectionError("Failed to connect to Base RPC.")
            
        self.account = self.web3.eth.account.from_key(private_key)
        self.wallet_address = self.account.address
        
        # Initialize Contracts
        self.exchange = self.web3.eth.contract(address=self.EXCHANGE_ADDRESS, abi=self.EXCHANGE_ABI)
        self.usdc = self.web3.eth.contract(address=self.USDC_ADDRESS, abi=self.USDC_ABI)
        self.registry = self.web3.eth.contract(address=self.KYA_REGISTRY_ADDRESS, abi=self.KYA_ABI)
        
        print(f"🌲 Pine Tree Agent Client Initialized: {self.wallet_address}")
        self.check_kya_status()

    def check_kya_status(self) -> bool:
        """Checks if the bot's wallet is officially whitelisted in the KYA Registry."""
        try:
            is_verified = self.registry.functions.checkAgentStatus(self.wallet_address).call()
            if is_verified:
                print("✅ KYA STATUS: Verified Agent (VIP Routing Enabled)")
            else:
                print("⚠️ KYA STATUS: Standard Wallet (Not registered for Agentic gas benefits)")
            return is_verified
        except Exception as e:
            print(f"Error checking KYA status: {e}")
            return False

    def get_market_data(self, market_id: int) -> dict:
        """Fetches live liquidity pool data for a specific market ID."""
        data = self.exchange.functions.getMarket(market_id).call()
        return {
            "initialized": data[0],
            "resolved": data[1],
            "canceled": data[2],
            "result": data[3],
            "yesPool": self.web3.from_wei(data[4], 'mwei'), # USDC is 6 decimals
            "noPool": self.web3.from_wei(data[5], 'mwei'),
            "deadline": data[6]
        }

    def allocate_position(self, market_id: int, is_yes: bool, usdc_amount: float):
        """Routes a transaction to the Pine Tree Exchange."""
        amount_mwei = int(usdc_amount * (10**6))
        
        # Check USDC Balance
        balance = self.usdc.functions.balanceOf(self.wallet_address).call()
        if balance < amount_mwei:
            raise ValueError(f"Insufficient USDC balance. Have {balance / 10**6}, need {usdc_amount}")

        nonce = self.web3.eth.get_transaction_count(self.wallet_address)

        # 1. Approve USDC
        print(f"Approving {usdc_amount} USDC for Market {market_id}...")
        approve_txn = self.usdc.functions.approve(self.EXCHANGE_ADDRESS, amount_mwei).build_transaction({
            'chainId': 8453,
            'gas': 100000,
            'gasPrice': self.web3.eth.gas_price,
            'nonce': nonce,
        })
        signed_approve = self.web3.eth.account.sign_transaction(approve_txn, private_key=self.account.key)
        self.web3.eth.send_raw_transaction(signed_approve.raw_transaction)
        
        # 2. Execute Stake
        print(f"Executing allocation to {'YES' if is_yes else 'NO'} pool...")
        nonce += 1 # Increment nonce for second tx
        stake_txn = self.exchange.functions.placeBet(market_id, is_yes, amount_mwei).build_transaction({
            'chainId': 8453,
            'gas': 250000,
            'gasPrice': self.web3.eth.gas_price,
            'nonce': nonce,
        })
        signed_stake = self.web3.eth.account.sign_transaction(stake_txn, private_key=self.account.key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_stake.raw_transaction)
        
        print(f"✅ Allocation Successful! TX: {self.web3.to_hex(tx_hash)}")
        return self.web3.to_hex(tx_hash)
