"""Cart routes — database-backed cart with stock reservation."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..extensions import db
from ..models.item import Item
from ..models.cart_item import CartItem
from ..repositories import ItemRepo

cart_bp = Blueprint("cart", __name__)


@cart_bp.route("/", methods=["GET"])
@login_required
def view_cart():
    from flask import render_template
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    items_in_cart = []
    total = 0
    for ci in cart_items:
        if not ci.is_expired:
            subtotal = float(ci.item.price) * ci.quantity
            total += subtotal
            items_in_cart.append({"item": ci.item, "qty": ci.quantity, "subtotal": subtotal})
    return render_template("cart.html", cart_items=items_in_cart, total=total)


@cart_bp.route("/add", methods=["POST"])
@login_required
def add():
    data = request.get_json() or {}
    item_id = int(data.get("item_id", 0))
    qty = int(data.get("qty", 1))
    if qty <= 0 or not item_id:
        return jsonify(success=False, message="Invalid input"), 400

    item = Item.query.filter_by(id=item_id, is_active=True).first()
    if not item:
        return jsonify(success=False, message="Item not available"), 404

    # Decrement stock immediately (reservation)
    rows_updated = ItemRepo.decrement_stock_atomic(item_id, qty)
    if rows_updated == 0:
        return jsonify(success=False, message="Out of stock"), 400

    ci = CartItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if ci:
        ci.quantity += qty
    else:
        ci = CartItem(user_id=current_user.id, item_id=item_id, quantity=qty)
        db.session.add(ci)
        
    # Reset expiration for the entire cart
    all_ci = CartItem.query.filter_by(user_id=current_user.id).all()
    for c in all_ci:
        c.reset_expiration()
        
    db.session.commit()
    
    # Calculate count
    cart_count = sum([c.quantity for c in CartItem.query.filter_by(user_id=current_user.id).all()])
    return jsonify(success=True, cart_count=cart_count, message=f"Added {item.name} to cart!")


@cart_bp.route("/update", methods=["POST"])
@login_required
def update():
    """Update quantity and restore/deduct difference in stock."""
    data = request.get_json() or {}
    item_id = int(data.get("item_id", 0))
    new_qty = int(data.get("qty", 0))
    
    ci = CartItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if not ci:
        return jsonify(success=False), 404
        
    diff = new_qty - ci.quantity
    
    if new_qty <= 0:
        # Restore stock and delete
        Item.query.filter_by(id=item_id).update({"stock_quantity": Item.stock_quantity + ci.quantity})
        db.session.delete(ci)
    elif diff > 0:
        # Trying to add more
        rows_updated = ItemRepo.decrement_stock_atomic(item_id, diff)
        if rows_updated == 0:
            return jsonify(success=False, message="Not enough stock"), 400
        ci.quantity = new_qty
    elif diff < 0:
        # Reducing quantity, restore stock
        Item.query.filter_by(id=item_id).update({"stock_quantity": Item.stock_quantity + abs(diff)})
        ci.quantity = new_qty
        
    # Reset expiration
    all_ci = CartItem.query.filter_by(user_id=current_user.id).all()
    for c in all_ci:
        c.reset_expiration()
        
    db.session.commit()
    return jsonify(success=True)


@cart_bp.route("/remove", methods=["POST"])
@login_required
def remove():
    data = request.get_json() or {}
    item_id = int(data.get("item_id", 0))
    ci = CartItem.query.filter_by(user_id=current_user.id, item_id=item_id).first()
    if ci:
        # Restore stock
        Item.query.filter_by(id=item_id).update({"stock_quantity": Item.stock_quantity + ci.quantity})
        db.session.delete(ci)
        db.session.commit()
    return jsonify(success=True)


@cart_bp.route("/count", methods=["GET"])
def count():
    if not current_user.is_authenticated:
        return jsonify(count=0)
    cart_count = sum([c.quantity for c in CartItem.query.filter_by(user_id=current_user.id).all() if not c.is_expired])
    return jsonify(count=cart_count)
