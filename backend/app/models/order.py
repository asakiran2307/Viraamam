"""Order model."""
from datetime import datetime
from ..extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(
        db.Enum("pending", "paid", "preparing", "completed", "cancelled", name="order_status"),
        nullable=False,
        default="pending",
    )
    razorpay_order_id = db.Column(db.String(100), nullable=True, unique=True)
    razorpay_payment_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="orders")
    order_items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = db.relationship("Payment", back_populates="order", uselist=False)

    def __repr__(self):
        return f"<Order #{self.id} {self.status}>"
