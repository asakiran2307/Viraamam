"""Cart routes — server-side cart stored in session."""
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from ..models.item import Item

cart_bp = Blueprint("cart", __name__)


def get_cart() -> dict:
    return session.get("cart", {})


def save_cart(cart: dict):
    session["cart"] = cart
    session.modified = True


@cart_bp.route("/", methods=["GET"])
@login_required
def view_cart():
    from flask import render_template
    cart = get_cart()
    items_in_cart = []
    total = 0
    for item_id_str, qty in cart.items():
        item = Item.query.filter_by(id=int(item_id_str), is_active=True).first()
        if item:
            subtotal = float(item.price) * qty
            total += subtotal
            items_in_cart.append({"item": item, "qty": qty, "subtotal": subtotal})
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
    if item.stock_quantity == 0:
        return jsonify(success=False, message="Out of stock"), 400

    cart = get_cart()
    current_qty = int(cart.get(str(item_id), 0))
    new_qty = min(current_qty + qty, item.stock_quantity)
    cart[str(item_id)] = new_qty
    save_cart(cart)
    cart_count = sum(cart.values())
    return jsonify(success=True, cart_count=cart_count, message=f"Added {item.name} to cart!")


@cart_bp.route("/update", methods=["POST"])
@login_required
def update():
    data = request.get_json() or {}
    item_id = str(int(data.get("item_id", 0)))
    qty = int(data.get("qty", 0))
    cart = get_cart()
    if qty <= 0:
        cart.pop(item_id, None)
    else:
        item = Item.query.filter_by(id=int(item_id), is_active=True).first()
        if not item:
            return jsonify(success=False), 404
        cart[item_id] = min(qty, item.stock_quantity)
    save_cart(cart)
    return jsonify(success=True)


@cart_bp.route("/remove", methods=["POST"])
@login_required
def remove():
    data = request.get_json() or {}
    item_id = str(int(data.get("item_id", 0)))
    cart = get_cart()
    cart.pop(item_id, None)
    save_cart(cart)
    return jsonify(success=True)


@cart_bp.route("/count", methods=["GET"])
def count():
    cart = get_cart()
    return jsonify(count=sum(cart.values()))
