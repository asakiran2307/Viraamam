"""Item model with BYTEA image storage."""
from datetime import datetime
from ..extensions import db


class Item(db.Model):
    __tablename__ = "items"
    __table_args__ = (
        db.CheckConstraint("stock_quantity >= 0", name="ck_items_stock_non_negative"),
        db.Index("ix_items_category_active", "category_id", "is_active"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True, index=True)
    image_data = db.Column(db.LargeBinary, nullable=True)
    image_mime_type = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship("Category", back_populates="items")
    order_items = db.relationship("OrderItem", back_populates="item", lazy="dynamic")

    def __repr__(self):
        return f"<Item {self.name} ₹{self.price}>"

    @property
    def in_stock(self):
        return self.stock_quantity > 0

    @property
    def low_stock(self):
        return 0 < self.stock_quantity <= 5
