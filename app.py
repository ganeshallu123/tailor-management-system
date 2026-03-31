import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Shop, Customer, Order, OrderItem, Measurement, Payment, ItemTemplate

app = Flask(__name__)
# Use a secure secret key in production!
app.config['SECRET_KEY'] = 'dev-secret-key-tailor-app'
# Use SQLite for local development
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tailor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(shop_id):
    return Shop.query.get(int(shop_id))

# Context processor to inject shop details into all templates
@app.context_processor
def inject_shop():
    if current_user.is_authenticated:
        return {'shop': current_user}
    return {}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    # Check if a shop exists, if not, create a default one for first-time use
    shop = Shop.query.first()
    if not shop:
        shop = Shop(username='admin', password_hash=generate_password_hash('admin'))
        db.session.add(shop)
        db.session.commit()
        flash('Default account created! Use admin / admin to login.', 'info')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = Shop.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if not user.is_setup_complete:
                return redirect(url_for('setup'))
            return redirect(url_for('index'))
        flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    if current_user.is_setup_complete:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        current_user.owner_name = request.form.get('owner_name')
        current_user.phone = request.form.get('phone')
        current_user.shop_name = request.form.get('shop_name')
        current_user.shop_address = request.form.get('shop_address')
        current_user.currency_symbol = request.form.get('currency_symbol', '$')
        
        tax = request.form.get('tax_settings')
        if tax:
            current_user.tax_settings = float(tax)
            
        current_user.is_setup_complete = True
        db.session.commit()
        
        flash('Setup complete! Welcome to your Dashboard.', 'success')
        return redirect(url_for('index'))
        
    return render_template('setup.html')

@app.route('/')
@login_required
def index():
    if not current_user.is_setup_complete:
        return redirect(url_for('setup'))
    
    # Render dashboard
    return render_template('dashboard.html')

from flask import jsonify

@app.route('/create_order')
@login_required
def create_order():
    return render_template('create_order.html')

@app.route('/api/orders', methods=['GET', 'POST'])
@login_required
def api_orders():
    if request.method == 'GET':
        status = request.args.get('status', 'Pending')
        query = request.args.get('q', '').lower()
        orders = Order.query.filter_by(status=status).all()
        # manual filter for demo
        result = []
        for o in orders:
            if query and query not in o.customer.name.lower() and query not in o.customer.phone:
                continue
            result.append({
                'id': o.id, 'customer_name': o.customer.name, 'phone': o.customer.phone,
                'total': o.total, 'due': o.due, 'date': o.order_date.strftime('%Y-%m-%d'),
                'delivery_date': o.delivery_date.strftime('%Y-%m-%d') if o.delivery_date else ''
            })
        return jsonify(result)
        
    # POST order creation
    data = request.json
    customer_id = data.get('customer_id')
    if not customer_id:
        # Create new customer
        customer = Customer(name=data['customer_name'], phone=data['customer_phone'], address=data.get('customer_address'))
        db.session.add(customer)
        db.session.commit()
        customer_id = customer.id
        
    order = Order(
        customer_id=customer_id,
        subtotal=data.get('subtotal', 0),
        tax_amount=data.get('tax_amount', 0),
        discount=data.get('discount', 0),
        total=data.get('total', 0),
        paid=data.get('paid', 0),
        due=data.get('due', 0),
        notes=data.get('notes', ''),
    )
    if 'delivery_date' in data and data['delivery_date']:
        order.delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d')
    if 'trial_date' in data and data['trial_date']:
        order.trial_date = datetime.strptime(data['trial_date'], '%Y-%m-%d')

    db.session.add(order)
    db.session.commit()
    
    # Save Items
    for item in data.get('items', []):
        order_item = OrderItem(order_id=order.id, item_name=item['name'], quantity=item['quantity'], price=item['price'])
        db.session.add(order_item)
        db.session.commit()
        
        # Save Measurements
        for m_key, m_val in item.get('measurements', {}).items():
            db.session.add(Measurement(order_item_id=order_item.id, field_name=m_key, field_value=m_val))
            
    # Save Advance Payment if any
    if data.get('paid', 0) > 0:
        db.session.add(Payment(order_id=order.id, amount=data['paid'], payment_mode=data.get('payment_mode', 'Cash')))
        
    db.session.commit()
    return jsonify({'success': True, 'order_id': order.id, 'customer_phone': data.get('customer_phone') or Customer.query.get(customer_id).phone}), 201

@app.route('/api/customers', methods=['GET'])
@login_required
def api_customers():
    q = request.args.get('q', '').lower()
    customers = Customer.query.all()
    res = []
    for c in customers:
        if q and q not in c.name.lower() and q not in c.phone:
            continue
        res.append({'id': c.id, 'name': c.name, 'phone': c.phone, 'address': c.address})
    return jsonify(res)

@app.route('/api/items', methods=['GET', 'POST'])
@login_required
def api_items():
    if request.method == 'GET':
        items = ItemTemplate.query.all()
        return jsonify([{'id': i.id, 'name': i.name, 'category': i.category, 'default_price': i.default_price} for i in items])
        
    # POST to add reusable item
    data = request.json
    item = ItemTemplate(name=data['name'], category=data.get('category', ''), default_price=data.get('default_price', 0))
    db.session.add(item)
    db.session.commit()
    return jsonify({'id': item.id, 'name': item.name, 'success': True}), 201

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
