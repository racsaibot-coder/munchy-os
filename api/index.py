import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from supabase import create_client, Client

app = Flask(__name__)

# CONFIG (In production, move these to Vercel Environment Variables)
SUPABASE_URL = "https://mtscvmxqhigyijcsozgd.supabase.co"
SUPABASE_KEY = "sb_publishable_ThXosDHFvZjyk02iWoFqXQ_dAVDKGVE"

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    return redirect(url_for('shop'))

@app.route('/shop')
def shop():
    try:
        response = supabase.table('inventory').select("*").order('stock', desc=True).execute()
        inventory = response.data
    except Exception as e:
        print(f"DB Error: {e}")
        inventory = []
    return render_template('shop.html', inventory=inventory)

@app.route('/admin')
def admin():
    try:
        # Fetch Inventory
        inv_res = supabase.table('inventory').select("*").execute()
        inventory = inv_res.data
        
        # Fetch Orders
        ord_res = supabase.table('orders').select("*").order('created_at', desc=True).execute()
        orders = ord_res.data
        
        # Calc Stats
        total_profit = 0
        items_sold = 0
        revenue = 0
        
        for o in orders:
            if o['status'] == 'paid':
                items_sold += 1
                revenue += float(o['price'])
                # Find cost of item to calc profit (Simplified: using current cost)
                # In a robust system, we'd store cost at time of sale.
                item = next((i for i in inventory if i['name'] == o['item_name']), None)
                if item:
                    cost = float(item['cost'])
                    total_profit += (float(o['price']) - cost)

    except Exception as e:
        print(f"DB Error: {e}")
        inventory = []
        orders = []
        total_profit = 0
        items_sold = 0
        revenue = 0

    return render_template('admin.html', inventory=inventory, orders=orders, stats={
        "profit": f"{total_profit:.2f}",
        "revenue": f"{revenue:.2f}",
        "sold": items_sold
    })

@app.route('/api/reserve', methods=['POST'])
def reserve():
    data = request.json
    item_name = data.get('item_name')
    student_name = data.get('student_name')
    price = data.get('price')
    
    # 1. Create Order
    order_data = {
        "student_name": student_name,
        "item_name": item_name,
        "price": price,
        "status": "pending"
    }
    supabase.table('orders').insert(order_data).execute()
    
    # 2. Decrement Stock
    # Note: In a real app, use RPC for atomicity. For MVP, we fetch-update.
    # We rely on the client to refresh, but let's try a direct decrement if possible?
    # Supabase doesn't support 'increment' in simple client easily without RPC.
    # We'll just assume stock management is loose for High School.
    # Update: Let's fetch current stock first.
    
    res = supabase.table('inventory').select('stock, id').eq('name', item_name).execute()
    if res.data:
        current = res.data[0]['stock']
        new_stock = max(0, current - 1)
        supabase.table('inventory').update({'stock': new_stock}).eq('id', res.data[0]['id']).execute()

    return jsonify({"success": True})

@app.route('/api/add_item', methods=['POST'])
def add_item():
    data = request.json
    item_data = {
        "name": data.get('name'),
        "cost": float(data.get('cost')),
        "price": float(data.get('price')),
        "stock": int(data.get('stock')),
        "image_url": data.get('image_url')
    }
    supabase.table('inventory').insert(item_data).execute()
    return jsonify({"success": True})

@app.route('/api/mark_paid', methods=['POST'])
def mark_paid():
    data = request.json
    order_id = data.get('id')
    supabase.table('orders').update({"status": "paid"}).eq("id", order_id).execute()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)