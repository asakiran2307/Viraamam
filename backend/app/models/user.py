"""User model."""
from datetime import datetime
from typing import Optional
from flask_login import UserMixin
from ..extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("customer", "admin", name="user_role"), nullable=False, default="customer")
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    orders = db.relationship("Order", back_populates="user", lazy="dynamic")

    def __init__(
        self,
        name: str,
        email: str,
        password_hash: str,
        role: str = "customer",
        phone: Optional[str] = None,
        is_active: bool = True,
    ) -> None:
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.phone = phone
        self.is_active = is_active

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
