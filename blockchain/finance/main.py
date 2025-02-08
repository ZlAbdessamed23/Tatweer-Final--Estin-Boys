from flask import Flask, request, jsonify
import hashlib
import json
import time
from supabase import create_client
from datetime import datetime

app = Flask(__name__)

class SupabaseConfig:
    def __init__(self):
        self.url = None
        self.key = None
        self.table_name = None
        self.client = None
        self.is_configured = False

    def configure(self, url, key, table_name):
        self.url = url
        self.key = key
        self.table_name = table_name
        self.client = create_client(self.url, self.key)
        self.is_configured = True
        return {"status": "success", "message": "Supabase configured successfully"}

class BlockchainFinance:
    def __init__(self):
        self.transactions = []
        self.contracts = {}
        
    def add_transaction(self, transaction):
        transaction_hash = hashlib.sha256(
            json.dumps(transaction, sort_keys=True).encode()
        ).hexdigest()
        
        self.transactions.append({
            "hash": transaction_hash,
            "timestamp": time.time(),
            "data": transaction
        })
        return transaction_hash

    def create_contract(self, contract_data, supabase_config):
        if not supabase_config.is_configured:
            return {"status": "error", "message": "Supabase not configured"}

        try:
            # Generate contract ID
            contract_id = hashlib.sha256(
                f"{contract_data['client_id']}:{time.time()}".encode()
            ).hexdigest()[:12]
            
            # Calculate required budget
            total_budget = contract_data['price'] * contract_data['quantity']
            
            # Create contract record
            contract_record = {
                "contract_id": contract_id,
                "client_id": contract_data['client_id'],
                "is_need_stock": contract_data['is_need_stock'],
                "price": contract_data['price'],
                "quantity": contract_data['quantity'],
                "total_budget": total_budget,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            # Store in Supabase
            response = supabase_config.client.table(supabase_config.table_name)\
                .insert(contract_record)\
                .execute()
            
            # Create blockchain transaction
            transaction = {
                "type": "contract_created",
                "contract_id": contract_id,
                **contract_record
            }
            
            transaction_hash = self.add_transaction(transaction)
            
            # Store contract locally
            self.contracts[contract_id] = contract_record
            
            return {
                "status": "success",
                "transaction_hash": transaction_hash,
                "contract_id": contract_id,
                "total_budget": total_budget,
                "details": contract_record
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def process_payment(self, contract_id, payment_amount, supabase_config):
        if not supabase_config.is_configured:
            return {"status": "error", "message": "Supabase not configured"}

        try:
            contract = self.contracts.get(contract_id)
            if not contract:
                return {"status": "error", "message": "Contract not found"}
            
            if payment_amount < contract['total_budget']:
                return {"status": "error", "message": "Insufficient payment amount"}
            
            # Update contract status
            response = supabase_config.client.table(supabase_config.table_name)\
                .update({"status": "paid"})\
                .eq("contract_id", contract_id)\
                .execute()
            
            # Create payment transaction
            transaction = {
                "type": "payment_processed",
                "contract_id": contract_id,
                "payment_amount": payment_amount,
                "timestamp": time.time()
            }
            
            transaction_hash = self.add_transaction(transaction)
            
            # Update local contract
            contract['status'] = 'paid'
            
            return {
                "status": "success",
                "transaction_hash": transaction_hash,
                "contract_id": contract_id,
                "payment_amount": payment_amount
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Initialize global configurations
supabase_config = SupabaseConfig()
blockchain_finance = BlockchainFinance()

@app.route('/configure', methods=['POST'])
def configure_supabase():
    data = request.get_json()
    if not data or 'supabase_url' not in data or 'supabase_key' not in data or 'table_name' not in data:
        return jsonify({"error": "Missing configuration parameters"}), 400
    
    try:
        result = supabase_config.configure(
            data['supabase_url'],
            data['supabase_key'],
            data['table_name']
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/contract/create', methods=['POST'])
def create_contract():
    if not supabase_config.is_configured:
        return jsonify({"error": "Supabase not configured"}), 400
    
    data = request.get_json()
    required_fields = ['client_id', 'is_need_stock', 'price', 'quantity']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    result = blockchain_finance.create_contract(data, supabase_config)
    return jsonify(result)

@app.route('/contract/<contract_id>/payment', methods=['POST'])
def process_payment(contract_id):
    if not supabase_config.is_configured:
        return jsonify({"error": "Supabase not configured"}), 400
    
    data = request.get_json()
    if not data or 'payment_amount' not in data:
        return jsonify({"error": "Payment amount required"}), 400
    
    result = blockchain_finance.process_payment(
        contract_id, 
        float(data['payment_amount']), 
        supabase_config
    )
    return jsonify(result)

@app.route('/transactions', methods=['GET'])
def get_transactions():
    return jsonify({
        "total_transactions": len(blockchain_finance.transactions),
        "transactions": blockchain_finance.transactions
    })

@app.route('/contracts', methods=['GET'])
def get_contracts():
    return jsonify({
        "total_contracts": len(blockchain_finance.contracts),
        "contracts": blockchain_finance.contracts
    })

if __name__ == '__main__':
    app.run(port=5003)