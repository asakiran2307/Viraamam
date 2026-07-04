"""Repository layer — industry-standard data access using SQLAlchemy 2.0 select() API.

All database reads go through here. Routes never call Model.query directly.
This separates data access from business logic (Repository Pattern).

SQLAlchemy 2.0 style:
  db.session.execute(select(Model).where(...)).scalars().all()
  db.session.get(Model, pk)
  db.session.execute(update(Model).where(...).values(...))
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import select, update, func, and_, or_

from .extensions import db
from .models.item import Item
from .models.category import Category
from .models.order import Order
from .models.order_item import OrderItem
from .models.user import User
from .models.advertisement import Advertisement
from .models.ambience import AmbiencePhoto
from .models.payment import Payment



# ── Item Repository ───────────────────────────────────────────────────────────

class ItemRepo:

    @staticmethod
    def get_by_id(item_id: int) -> Optional[Item]:
        return db.session.get(Item, item_id)

    @staticmethod
    def get_active_by_id(item_id: int) -> Optional[Item]:
        stmt = select(Item).where(Item.id == item_id, Item.is_active == True)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_image(item_id: int):
        """Fetch only image columns — avoids loading large blobs unnecessarily."""
        stmt = (
            select(Item.id, Item.image_data, Item.image_mime_type, Item.updated_at)
            .where(Item.id == item_id)
        )
        return db.session.execute(stmt).one_or_none()

    @staticmethod
    def list_active(
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 12,
    ):
        """Paginated, filtered list of active items for the public catalog."""
        stmt = select(Item).where(Item.is_active == True)
        if category_id is not None:
            stmt = stmt.where(Item.category_id == category_id)
        if search:
            stmt = stmt.where(Item.name.ilike(f"%{search}%"))
        stmt = stmt.order_by(Item.created_at.desc())
        return db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    @staticmethod
    def list_all_admin(search: Optional[str] = None, page: int = 1, per_page: int = 20):
        """All items (including inactive) for admin panel."""
        stmt = select(Item)
        if search:
            stmt = stmt.where(Item.name.ilike(f"%{search}%"))
        stmt = stmt.order_by(Item.created_at.desc())
        return db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    @staticmethod
    def featured(limit: int = 8):
        stmt = select(Item).where(Item.is_active == True).order_by(Item.created_at.desc()).limit(limit)
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def count_active() -> int:
        stmt = select(func.count(Item.id)).where(Item.is_active == True)
        return db.session.execute(stmt).scalar_one()

    @staticmethod
    def count_low_stock() -> int:
        stmt = select(func.count(Item.id)).where(
            Item.stock_quantity <= 5,
            Item.stock_quantity > 0,
            Item.is_active == True,
        )
        return db.session.execute(stmt).scalar_one()

    @staticmethod
    def count_out_of_stock() -> int:
        stmt = select(func.count(Item.id)).where(
            Item.stock_quantity == 0,
            Item.is_active == True,
        )
        return db.session.execute(stmt).scalar_one()

    @staticmethod
    def decrement_stock_atomic(item_id: int, qty: int) -> int:
        """
        Atomic conditional stock decrement using SQLAlchemy 2.0 update().
        Returns number of rows updated (0 = out of stock / insufficient).
        Industry pattern: single UPDATE prevents race conditions without SELECT.
        """
        stmt = (
            update(Item)
            .where(Item.id == item_id, Item.stock_quantity >= qty)
            .values(stock_quantity=Item.stock_quantity - qty)
            .execution_options(synchronize_session=False)
        )
        result = db.session.execute(stmt)
        return result.rowcount


# ── Category Repository ───────────────────────────────────────────────────────

class CategoryRepo:

    @staticmethod
    def get_by_id(cat_id: int) -> Optional[Category]:
        return db.session.get(Category, cat_id)

    @staticmethod
    def get_by_slug(slug: str) -> Optional[Category]:
        stmt = select(Category).where(Category.slug == slug)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def slug_exists(slug: str) -> bool:
        stmt = select(func.count(Category.id)).where(Category.slug == slug)
        return db.session.execute(stmt).scalar_one() > 0

    @staticmethod
    def all() -> list[Category]:
        stmt = select(Category).order_by(Category.name)
        return db.session.execute(stmt).scalars().all()


# ── Order Repository ──────────────────────────────────────────────────────────

class OrderRepo:

    @staticmethod
    def get_by_id(order_id: int) -> Optional[Order]:
        return db.session.get(Order, order_id)

    @staticmethod
    def get_by_razorpay_id(rp_order_id: str) -> Optional[Order]:
        stmt = select(Order).where(Order.razorpay_order_id == rp_order_id)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_for_user(user_id: int, page: int = 1, per_page: int = 10):
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        return db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    @staticmethod
    def all_admin(page: int = 1, per_page: int = 20, status: Optional[str] = None):
        stmt = select(Order).order_by(Order.created_at.desc())
        if status:
            stmt = stmt.where(Order.status == status)
        return db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    @staticmethod
    def recent(limit: int = 10) -> list[Order]:
        stmt = select(Order).order_by(Order.created_at.desc()).limit(limit)
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def count_today() -> int:
        today = datetime.utcnow().date()
        stmt = select(func.count(Order.id)).where(func.date(Order.created_at) == today)
        return db.session.execute(stmt).scalar_one()

    @staticmethod
    def revenue_today() -> float:
        today = datetime.utcnow().date()
        stmt = select(
            func.coalesce(func.sum(Order.total_amount), 0)
        ).where(
            func.date(Order.created_at) == today,
            Order.status.in_(["paid", "completed"]),
        )
        return float(db.session.execute(stmt).scalar_one())

    @staticmethod
    def update_status(order_id: int, status: str) -> None:
        stmt = (
            update(Order)
            .where(Order.id == order_id)
            .values(status=status)
            .execution_options(synchronize_session=False)
        )
        db.session.execute(stmt)


# ── OrderItem Repository ──────────────────────────────────────────────────────

class OrderItemRepo:

    @staticmethod
    def for_order(order_id: int) -> list:
        """Return (item_id, quantity) tuples for an order — minimal columns."""
        stmt = (
            select(OrderItem.item_id, OrderItem.quantity)
            .where(OrderItem.order_id == order_id)
        )
        return db.session.execute(stmt).all()


# ── User Repository ───────────────────────────────────────────────────────────

class UserRepo:

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def email_exists(email: str) -> bool:
        stmt = select(func.count(User.id)).where(User.email == email)
        return db.session.execute(stmt).scalar_one() > 0

    @staticmethod
    def all_admin(page: int = 1, per_page: int = 30):
        stmt = select(User).order_by(User.created_at.desc())
        return db.paginate(stmt, page=page, per_page=per_page, error_out=False)


# ── Advertisement Repository ──────────────────────────────────────────────────

class AdRepo:

    @staticmethod
    def get_by_id(ad_id: int) -> Optional[Advertisement]:
        return db.session.get(Advertisement, ad_id)

    @staticmethod
    def active_today() -> list[Advertisement]:
        today = date.today()
        stmt = (
            select(Advertisement)
            .where(
                Advertisement.is_active == True,
                Advertisement.start_date <= today,
                Advertisement.end_date >= today,
            )
            .order_by(Advertisement.display_order)
        )
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def all_admin() -> list[Advertisement]:
        stmt = select(Advertisement).order_by(Advertisement.display_order)
        return db.session.execute(stmt).scalars().all()


# ── Ambience Repository ───────────────────────────────────────────────────────

class AmbienceRepo:

    @staticmethod
    def get_by_id(photo_id: int) -> Optional[AmbiencePhoto]:
        return db.session.get(AmbiencePhoto, photo_id)

    @staticmethod
    def all_active() -> list[AmbiencePhoto]:
        stmt = (
            select(AmbiencePhoto)
            .where(AmbiencePhoto.is_active == True)
            .order_by(AmbiencePhoto.display_order)
        )
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def all_admin() -> list[AmbiencePhoto]:
        stmt = select(AmbiencePhoto).order_by(AmbiencePhoto.display_order)
        return db.session.execute(stmt).scalars().all()


# ── Payment Repository ────────────────────────────────────────────────────────

class PaymentRepo:

    @staticmethod
    def get_by_order_id(order_id: int) -> Optional[Payment]:
        stmt = select(Payment).where(Payment.order_id == order_id)
        return db.session.execute(stmt).scalar_one_or_none()
