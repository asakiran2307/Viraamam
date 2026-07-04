"""Stock service — concurrency-safe, atomic stock management.

Uses SQLAlchemy 2.0 update() via ItemRepo.decrement_stock_atomic().
No raw SQL — the ORM generates:
  UPDATE items SET stock_quantity = stock_quantity - :qty
  WHERE id = :id AND stock_quantity >= :qty
"""
from ..extensions import db
from ..repositories import ItemRepo, OrderItemRepo


def decrement_stock_for_order(order_id: int) -> bool:
    """
    Atomically decrement stock for every item in an order.
    Returns True on full success, False if any item is out of stock
    (rolls back the whole transaction — all-or-nothing).
    """
    order_items = OrderItemRepo.for_order(order_id)

    for oi in order_items:
        rows_updated = ItemRepo.decrement_stock_atomic(oi.item_id, oi.quantity)
        if rows_updated == 0:
            db.session.rollback()
            return False

    db.session.commit()
    return True
