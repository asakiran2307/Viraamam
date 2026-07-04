"""Cart service — handles automated cleanup of expired carts."""
import logging
from datetime import datetime
from flask import current_app
from ..extensions import db
from ..models.item import Item
from ..models.cart_item import CartItem

logger = logging.getLogger(__name__)


def cleanup_expired_carts():
    """Find carts that have expired, restore stock, and delete the cart item."""
    try:
        now = datetime.utcnow()
        expired_items = CartItem.query.filter(CartItem.expires_at < now).all()
        if not expired_items:
            return

        for ci in expired_items:
            # Restore stock
            Item.query.filter_by(id=ci.item_id).update({"stock_quantity": Item.stock_quantity + ci.quantity})
            db.session.delete(ci)
            
        db.session.commit()
        logger.info(f"Cleaned up {len(expired_items)} expired cart items and restored stock.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to cleanup expired carts: {e}")
