"""Checkout routes — handles placing orders directly without Razorpay."""
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from ..extensions import db
from ..models.order import Order
from ..models.order_item import OrderItem
from ..models.cart_item import CartItem
from ..services.telegram_service import send_telegram_notification

payments_bp = Blueprint("payments", __name__)


def _notify_admin(order):
    try:
        items_summary = "\n".join([f"- {oi.quantity}x {oi.item.name}" for oi in order.order_items])
        send_telegram_notification(order.id, float(order.total_amount), items_summary)
    except Exception as e:
        current_app.logger.error(f"Failed to format/send telegram notification: {e}")


@payments_bp.route("/place-order", methods=["POST"])
@login_required
def place_order():
    """Place the order directly, convert cart reservations to order items."""
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    # Filter out expired items just in case cleanup hasn't caught them
    valid_cart_items = [ci for ci in cart_items if not ci.is_expired]
    
    if not valid_cart_items:
        return jsonify(error="Your cart is empty or reservations expired"), 400

    total_amount = sum([float(ci.item.price) * ci.quantity for ci in valid_cart_items])

    # Create the order
    order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        status="paid"  # Direct checkout bypasses payment for now
    )
    db.session.add(order)
    db.session.flush()  # get order.id

    # Create OrderItems
    for ci in valid_cart_items:
        oi = OrderItem(
            order_id=order.id,
            item_id=ci.item_id,
            quantity=ci.quantity,
            price_at_purchase=ci.item.price
        )
        db.session.add(oi)
        db.session.delete(ci)  # Delete cart item (stock is already decremented!)
        
    db.session.commit()

    # Send telegram notification
    _notify_admin(order)

    return jsonify(success=True, order_id=order.id)
