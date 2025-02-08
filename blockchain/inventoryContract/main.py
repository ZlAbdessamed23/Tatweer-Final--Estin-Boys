# inventory_service.py
from flask import Flask, request, jsonify
import hashlib
import json
import time
from supabase import create_client

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

class BlockchainInventory:
    def __init__(self):
        self.inventory = {}
        self.products_cache = {}
        self.cache_timestamp = 0
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

    def update_stock(self, product_id, quantity, supabase_config):
        if not supabase_config.is_configured:
            return {"status": "error", "message": "Supabase not configured"}

        try:
            # Fetch product from Supabase
            response = supabase_config.client.table(supabase_config.table_name)\
                .select("*")\
                .eq("id", product_id)\
                .execute()
            
            if not response.data:
                return {"status": "error", "message": "Product not found"}
            
            product = response.data[0]
            
            # Update inventory
            if product_id not in self.inventory:
                self.inventory[product_id] = 0
            self.inventory[product_id] += quantity
            
            # Create blockchain transaction
            transaction = {
                "type": "stock_update",
                "product_id": product_id,
                "product_name": product["name"],
                "quantity_change": quantity,
                "new_quantity": self.inventory[product_id],
                "timestamp": time.time()
            }
            
            transaction_hash = self.add_transaction(transaction)
            
            return {
                "status": "success",
                "transaction_hash": transaction_hash,
                "product_id": product_id,
                "product_name": product["name"],
                "new_quantity": self.inventory[product_id],
                "blockchain_status": "confirmed"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Initialize global configurations
supabase_config = SupabaseConfig()
blockchain_inventory = BlockchainInventory()

# Route to configure Supabase
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
        return jsonify({"status": "error", "message": str(e)}), 500

# Route to update inventory
@app.route('/inventory/update', methods=['POST'])
def update_inventory():
    if not supabase_config.is_configured:
        return jsonify({"error": "Supabase not configured"}), 400
    
    data = request.get_json()
    if not data or 'isStock' not in data:
        return jsonify({"error": "Invalid data format"}), 400
    
    product_id = data.get('product_id')
    quantity = data.get('quantity', 0)
    
    if data['isStock'] == 1:
        result = blockchain_inventory.update_stock(product_id, quantity, supabase_config)
        return jsonify(result)
    return jsonify({"error": "Invalid stock operation"}), 400

# Route to get transaction history
@app.route('/transactions', methods=['GET'])
def get_transactions():
    return jsonify({
        "total_transactions": len(blockchain_inventory.transactions),
        "transactions": blockchain_inventory.transactions
    })

if __name__ == '__main__':
    app.run(port=5001)