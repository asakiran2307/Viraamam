"""Payment service — Razorpay HMAC verification."""
import hmac
import hashlib
from flask import current_app


def verify_razorpay_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    """Verify the HMAC-SHA256 signature from the Razorpay checkout callback."""
    secret = current_app.config["RAZORPAY_KEY_SECRET"]
    body = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, razorpay_signature)


def verify_webhook_signature(payload_body: bytes, signature: str) -> bool:
    """Verify the webhook signature using RAZORPAY_WEBHOOK_SECRET."""
    secret = current_app.config["RAZORPAY_WEBHOOK_SECRET"]
    if not secret:
        return False
    expected = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
