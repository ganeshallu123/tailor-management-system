from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Shop(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    owner_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    shop_name = db.Column(db.String(200), nullable=True)
    shop_address = db.Column(db.Text, nullable=True)
    currency_symbol = db.Column(db.String(10), default='$')
    tax_settings = db.Column(db.Float, default=0.0) # percentage
    is_setup_complete = db.Column(db.Boolean, default=False)
    
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    
    orders = db.relationship('Order', backref='customer', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Complete, Delivered
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    trial_date = db.Column(db.DateTime, nullable=True)
    delivery_date = db.Column(db.DateTime, nullable=True)
    
    # Billing
    subtotal = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    paid = db.Column(db.Float, default=0.0)
    due = db.Column(db.Float, default=0.0)
    
    notes = db.Column(db.Text, nullable=True)
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='order', lazy=True, cascade='all, delete-orphan')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False) # e.g. Shirt, Pant
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, default=0.0)
    
    measurements = db.relationship('Measurement', backref='order_item', lazy=True, cascade='all, delete-orphan')

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_item.id'), nullable=False)
    field_name = db.Column(db.String(50), nullable=False)   # e.g., Length, Chest
    field_value = db.Column(db.String(100), nullable=False) # e.g., 38", Cuffs (2)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_mode = db.Column(db.String(20), nullable=False) # Cash, UPI, Card
    date = db.Column(db.DateTime, default=datetime.utcnow)

class ItemTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    default_price = db.Column(db.Float, default=0.0)
