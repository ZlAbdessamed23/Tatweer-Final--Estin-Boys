# sales_service.py
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

class BlockchainSales:
    def __init__(self):
        self.sales = {}
        self.transactions = []
        
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

    def create_sale(self, sale_data, supabase_config):
        if not supabase_config.is_configured:
            return {"status": "error", "message": "Supabase not configured"}

        try:
            # Generate sale ID
            sale_id = hashlib.sha256(
                f"{sale_data['client_id']}:{time.time()}".encode()
            ).hexdigest()[:12]
            
            # Create sale record in Supabase
            sale_record = {
                "sale_id": sale_id,
                "client_id": sale_data['client_id'],
                "items": json.dumps(sale_data['items']),
                "total_amount": sale_data['total_amount'],
                "status": "created",
                "created_at": datetime.now().isoformat()
            }
            
            response = supabase_config.client.table(supabase_config.table_name)\
                .insert(sale_record)\
                .execute()
            
            # Create blockchain transaction
            transaction = {
                "type": "sale_created",
                "sale_id": sale_id,
                **sale_record
            }
            
            transaction_hash = self.add_transaction(transaction)
            
            return {
                "status": "success",
                "transaction_hash": transaction_hash,
                "sale_id": sale_id,
                "details": sale_record
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def update_sale_status(self, sale_id, new_status, supabase_config):
        if not supabase_config.is_configured:
            return {"status": "error", "message": "Supabase not configured"}

        try:
            # Update status in Supabase
            response = supabase_config.client.table(supabase_config.table_name)\
                .update({"status": new_status})\
                .eq("sale_id", sale_id)\
                .execute()
            
            if not response.data:
                return {"status": "error", "message": "Sale not found"}
            
            # Create blockchain transaction
            transaction = {
                "type": "sale_status_update",
                "sale_id": sale_id,
                "new_status": new_status,
                "timestamp": time.time()
            }
            
            transaction_hash = self.add_transaction(transaction)
            
            return {
                "status": "success",
                "transaction_hash": transaction_hash,
                "sale_id": sale_id,
                "new_status": new_status
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Initialize global configurations
supabase_config = SupabaseConfig()
blockchain_sales = BlockchainSales()

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

@app.route('/sale/create', methods=['POST'])
def create_sale():
    if not supabase_config.is_configured:
        return jsonify({"error": "Supabase not configured"}), 400
    
    data = request.get_json()
    if not data or 'isClient' not in data:
        return jsonify({"error": "Invalid data format"}), 400
    
    if data['isClient'] == 1:
        sale_data = {
            "client_id": data.get('client_id'),
            "items": data.get('items', []),
            "total_amount": sum(item.get('price', 0) * item.get('quantity', 0) 
                              for item in data.get('items', []))
        }
        result = blockchain_sales.create_sale(sale_data, supabase_config)
        return jsonify(result)
    return jsonify({"error": "Invalid sale operation"}), 400

@app.route('/sale/<sale_id>/status', methods=['PUT'])
def update_sale_status(sale_id):
    if not supabase_config.is_configured:
        return jsonify({"error": "Supabase not configured"}), 400
    
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "Invalid data format"}), 400
    
    result = blockchain_sales.update_sale_status(sale_id, data['status'], supabase_config)
    return jsonify(result)

@app.route('/transactions', methods=['GET'])
def get_transactions():
    return jsonify({
        "total_transactions": len(blockchain_sales.transactions),
        "transactions": blockchain_sales.transactions
    })

if __name__ == '__main__':
    app.run(port=5003)