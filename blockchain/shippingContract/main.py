# shipping_service.py
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

class BlockchainShipping:
    def __init__(self):
        self.shipments = {}
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

    def create_shipment(self, shipment_data, supabase_config):
        if not supabase_config.is_configured:
            return {"status": "error", "message": "Supabase not configured"}

        try:
            # Generate shipment ID
            shipment_id = hashlib.sha256(
                f"{shipment_data['from']}:{shipment_data['to']}:{time.time()}".encode()
            ).hexdigest()[:12]
            
            # Create shipment record in Supabase
            shipment_record = {
                "shipment_id": shipment_id,
                "from_location": shipment_data['from'],
                "to_location": shipment_data['to'],
                "items": json.dumps(shipment_data['items']),
                "status": "created",
                "created_at": datetime.now().isoformat()
            }
            
            response = supabase_config.client.table(supabase_config.table_name)\
                .insert(shipment_record)\
                .execute()
            
            # Create blockchain transaction
            transaction = {
                "type": "shipment_created",
                "shipment_id": shipment_id,
                **shipment_record
            }
            
            transaction_hash = self.add_transaction(transaction)
            
            return {
                "status": "success",
                "transaction_hash": transaction_hash,
                "shipment_id": shipment_id,
                "details": shipment_record
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def update_status(self, shipment_id, new_status, supabase_config):
        if not supabase_config.is_configured:
            return {"status": "error", "message": "Supabase not configured"}

        try:
            # Update status in Supabase
            response = supabase_config.client.table(supabase_config.table_name)\
                .update({"status": new_status})\
                .eq("shipment_id", shipment_id)\
                .execute()
            
            if not response.data:
                return {"status": "error", "message": "Shipment not found"}
            
            # Create blockchain transaction
            transaction = {
                "type": "shipment_status_update",
                "shipment_id": shipment_id,
                "new_status": new_status,
                "timestamp": time.time()
            }
            
            transaction_hash = self.add_transaction(transaction)
            
            return {
                "status": "success",
                "transaction_hash": transaction_hash,
                "shipment_id": shipment_id,
                "new_status": new_status
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Initialize global configurations
supabase_config = SupabaseConfig()
blockchain_shipping = BlockchainShipping()

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

@app.route('/shipment/create', methods=['POST'])
def create_shipment():
    if not supabase_config.is_configured:
        return jsonify({"error": "Supabase not configured"}), 400
    
    data = request.get_json()
    if not data or 'isShipment' not in data:
        return jsonify({"error": "Invalid data format"}), 400
    
    if data['isShipment'] == 1:
        shipment_data = {
            "from": data.get('from'),
            "to": data.get('to'),
            "items": data.get('items', [])
        }
        result = blockchain_shipping.create_shipment(shipment_data, supabase_config)
        return jsonify(result)
    return jsonify({"error": "Invalid shipment operation"}), 400

@app.route('/shipment/<shipment_id>/status', methods=['PUT'])
def update_shipment_status(shipment_id):
    if not supabase_config.is_configured:
        return jsonify({"error": "Supabase not configured"}), 400
    
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "Invalid data format"}), 400
    
    result = blockchain_shipping.update_status(shipment_id, data['status'], supabase_config)
    return jsonify(result)

@app.route('/transactions', methods=['GET'])
def get_transactions():
    return jsonify({
        "total_transactions": len(blockchain_shipping.transactions),
        "transactions": blockchain_shipping.transactions
    })

if __name__ == '__main__':
    app.run(port=5002)