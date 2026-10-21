"""Checkout routes — handles placing orders without marking them paid."""
import logging
from flask import Blueprint, jsonify, current_app
from flask_login import login_required, current_user
from ..extensions import db
from ..models.order import Order
from ..models.order_item import OrderItem
from ..models.cart_item import CartItem
from ..services.telegram_service import send_telegram_notification

payments_bp = Blueprint("payments", __name__)


def _notify_admin(order):
    try:
        items_summary = "\n".join(
            [f"- {oi.quantity}x {oi.item.name}" for oi in order.order_items]
        )
        send_telegram_notification(
            order.id, float(order.total_amount), items_summary
        )
    except Exception:
        current_app.logger.exception(
            "Failed to send Telegram notification for order %s", order.id
        )


@payments_bp.route("/place-order", methods=["POST"])
@login_required
def place_order():
    """Create an order from the user's reserved cart.

    This endpoint does not verify or collect a payment, so the order must remain
    pending. A verified payment callback/webhook is the only flow that should
    transition an order to 'paid'.
    """
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    valid_cart_items = [ci for ci in cart_items if not ci.is_expired]

    if not valid_cart_items:
        return jsonify(error="Your cart is empty or reservations expired"), 400

    # Compute totals from current database prices, never client-supplied values.
    total_amount = sum(
        (ci.item.price * ci.quantity for ci in valid_cart_items),
        start=0,
    )

    try:
        order = Order(
            user_id=current_user.id,
            total_amount=total_amount,
            status="pending",
        )
        db.session.add(order)
        db.session.flush()

        for ci in valid_cart_items:
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    item_id=ci.item_id,
                    quantity=ci.quantity,
                    price_at_purchase=ci.item.price,
                )
            )
            # Stock was reserved when the item was added to the cart.
            db.session.delete(ci)

        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Failed to create order for user %s", current_user.id
        )
        return jsonify(error="Unable to place your order. Please try again."), 500

    _notify_admin(order)
    return jsonify(success=True, order_id=order.id, status=order.status), 201
