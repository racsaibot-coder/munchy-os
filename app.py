from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)

# --- Config & Data Helpers ---
INVENTORY_FILE = 'inventory.json'
SALES_FILE = 'sales.json'

def load_json(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# --- Routes ---

@app.route('/')
def home():
    return redirect(url_for('shop'))

@app.route('/shop')
def shop():
    inventory = load_json(INVENTORY_FILE)
    # Only show items in stock
    available_items = [item for item in inventory if item.get('stock', 0) > 0]
    return render_template('shop.html', items=available_items)

@app.route('/admin')
def admin():
    inventory = load_json(INVENTORY_FILE)
    sales = load_json(SALES_FILE)
    
    # Calculate stats
    total_sales = sum(sale['price'] for sale in sales)
    total_profit = sum(sale['profit'] for sale in sales)
    items_sold = len(sales)
    
    return render_template('admin.html', 
                           inventory=inventory, 
                           stats={
                               'revenue': total_sales,
                               'profit': total_profit,
                               'sales_count': items_sold
                           })

# --- API Endpoints ---

@app.route('/api/reserve', methods=['POST'])
def reserve_item():
    data = request.json
    item_id = int(data.get('id'))
    student_name = data.get('name')
    
    inventory = load_json(INVENTORY_FILE)
    sales = load_json(SALES_FILE)
    
    # Find item
    item_index = next((i for i, item in enumerate(inventory) if item['id'] == item_id), None)
    
    if item_index is not None and inventory[item_index]['stock'] > 0:
        item = inventory[item_index]
        
        # Decrement stock
        inventory[item_index]['stock'] -= 1
        save_json(INVENTORY_FILE, inventory)
        
        # Record sale (reservation)
        sale = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "item_name": item['name'],
            "price": item['price'],
            "cost": item['cost'],
            "profit": item['price'] - item['cost'],
            "student": student_name,
            "status": "reserved"
        }
        sales.append(sale)
        save_json(SALES_FILE, sales)
        
        return jsonify({"success": True, "message": "Item reserved!"})
    
    return jsonify({"success": False, "message": "Out of stock or invalid item."}), 400

@app.route('/api/add_item', methods=['POST'])
def add_item():
    data = request.json
    inventory = load_json(INVENTORY_FILE)
    
    new_id = 1
    if inventory:
        new_id = max(item['id'] for item in inventory) + 1
        
    new_item = {
        "id": new_id,
        "name": data['name'],
        "image": data['image'] or "https://via.placeholder.com/150?text=No+Image",
        "cost": float(data['cost']),
        "price": float(data['price']),
        "stock": int(data['stock'])
    }
    
    inventory.append(new_item)
    save_json(INVENTORY_FILE, inventory)
    
    return jsonify({"success": True, "item": new_item})

@app.route('/api/delete_item', methods=['POST'])
def delete_item():
    data = request.json
    item_id = int(data.get('id'))
    inventory = load_json(INVENTORY_FILE)
    
    inventory = [item for item in inventory if item['id'] != item_id]
    save_json(INVENTORY_FILE, inventory)
    
    return jsonify({"success": True})

if __name__ == '__main__':
    # Run on 0.0.0.0 to be accessible on local network (e.g. from phone)
    app.run(debug=True, host='0.0.0.0', port=5000)
