"""CartItem model — tracks server-side carts for stock reservation."""
from datetime import datetime, timedelta
from ..extensions import db


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    # Cart item expires in 30 minutes. If older than this, stock is restored.
    expires_at = db.Column(db.DateTime, nullable=False, index=True)

    user = db.relationship("User", backref=db.backref("cart_items", cascade="all, delete-orphan"))
    item = db.relationship("Item", backref="cart_reservations")

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def reset_expiration(self):
        self.expires_at = datetime.utcnow() + timedelta(minutes=30)

    def __repr__(self):
        return f"<CartItem user={self.user_id} item={self.item_id} qty={self.quantity}>"
