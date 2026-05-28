from web3 import Web3
from eth_account import Account

class PineTreeAgentClient:
    """Core client for the PineTree agentic prediction market."""

    def __init__(self, rpc_url: str, private_key: str = None, contract_address: str = None, abi: list = None):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.abi = abi
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi)
        
        if private_key:
            self.account = Account.from_key(private_key)
            self.w3.eth.default_account = self.account.address
        else:
            self.account = None

    def get_market(self, market_id: int) -> dict:
        """Fetches the state of a specific market ID from the contract."""
        try:
            # getMarket returns: initialized, resolved, canceled, result, yesPool, noPool, deadline
            m = self.contract.functions.getMarket(market_id).call()
            
            if not m[0]: 
                return {"error": "Market not initialized."}
                
            yes_pool = m[4]
            no_pool = m[5]
            total_pool = yes_pool + no_pool
            
            return {
                "market_id": market_id,
                "initialized": m[0],
                "resolved": m[1],
                "canceled": m[2],
                "pool_yes": yes_pool,
                "pool_no": no_pool,
                "implied_prob_yes": yes_pool / total_pool if total_pool > 0 else 0.5,
                "deadline": m[6]
            }
        except Exception as e:
            return {"error": str(e)}

    def execute_position(self, market_id: int, outcome_yes: bool, amount_wei: int) -> str:
        """Signs and broadcasts a position locally using placeBet."""
        if not self.account:
            raise ValueError("Private key required for execution.")
            
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        base_fee = self.w3.eth.gas_price
        
        tx = self.contract.functions.placeBet(
            market_id, 
            outcome_yes, 
            amount_wei
        ).build_transaction({
            "chainId": 8453,
            "from": self.account.address,
            "nonce": nonce,
            "gasPrice": int(base_fee * 1.1)
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_bytes)
        return self.w3.to_hex(tx_hash)
