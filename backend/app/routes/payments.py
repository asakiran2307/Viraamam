"""Razorpay payment routes — order creation, verification, webhook."""
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, abort, current_app, session
from flask_login import login_required, current_user
import razorpay
from ..extensions import db
from ..models.order import Order
from ..models.payment import Payment
from ..services.order_service import create_order
from ..services.payment_service import verify_razorpay_signature, verify_webhook_signature
from ..services.stock_service import decrement_stock_for_order

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/create-order", methods=["POST"])
@login_required
def create_razorpay_order():
    """Create a Razorpay order from server-computed cart total."""
    cart = session.get("cart", {})
    if not cart:
        return jsonify(error="Cart is empty"), 400

    try:
        order = create_order(current_user.id, cart)
    except ValueError as e:
        return jsonify(error=str(e)), 400

    client = razorpay.Client(
        auth=(current_app.config["RAZORPAY_KEY_ID"], current_app.config["RAZORPAY_KEY_SECRET"])
    )
    amount_paise = int(order.total_amount * 100)
    rz_order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"viraamam_order_{order.id}",
    })

    order.razorpay_order_id = rz_order["id"]
    db.session.commit()

    return jsonify(
        order_id=rz_order["id"],
        amount=amount_paise,
        currency="INR",
        key=current_app.config["RAZORPAY_KEY_ID"],
        internal_order_id=order.id,
    )


@payments_bp.route("/verify", methods=["POST"])
@login_required
def verify_payment():
    """Verify payment signature from client callback."""
    data = request.get_json() or {}
    rz_order_id = data.get("razorpay_order_id", "")
    rz_payment_id = data.get("razorpay_payment_id", "")
    rz_signature = data.get("razorpay_signature", "")

    if not verify_razorpay_signature(rz_order_id, rz_payment_id, rz_signature):
        return jsonify(error="Payment verification failed"), 400

    order = Order.query.filter_by(razorpay_order_id=rz_order_id).first()
    if not order or order.user_id != current_user.id:
        abort(403)

    if order.status == "paid":
        session.pop("cart", None)
        return jsonify(success=True, order_id=order.id)

    order.razorpay_payment_id = rz_payment_id
    order.status = "paid"
    db.session.commit()

    if not decrement_stock_for_order(order.id):
        return jsonify(error="Stock issue — contact support"), 500

    payment = Payment(
        order_id=order.id,
        razorpay_order_id=rz_order_id,
        razorpay_payment_id=rz_payment_id,
        razorpay_signature=rz_signature,
        amount=order.total_amount,
        status="verified",
        verified_at=datetime.utcnow(),
    )
    db.session.add(payment)
    db.session.commit()
    session.pop("cart", None)
    return jsonify(success=True, order_id=order.id)


@payments_bp.route("/webhook", methods=["POST"])
def razorpay_webhook():
    """Webhook handler — source of truth for payment confirmation."""
    payload_bytes = request.get_data()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not verify_webhook_signature(payload_bytes, signature):
        abort(400)

    event = request.get_json(force=True)
    if event.get("event") != "payment.captured":
        return jsonify(status="ignored"), 200

    payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
    rz_order_id = payment_entity.get("order_id")
    rz_payment_id = payment_entity.get("id")

    order = Order.query.filter_by(razorpay_order_id=rz_order_id).first()
    if not order:
        return jsonify(status="order not found"), 200

    if order.status == "paid":
        return jsonify(status="already processed"), 200  # idempotent

    order.status = "paid"
    order.razorpay_payment_id = rz_payment_id
    db.session.commit()

    if not decrement_stock_for_order(order.id):
        current_app.logger.error(f"Stock decrement failed for order {order.id} from webhook")

    return jsonify(status="ok"), 200
