"""Order service — server-side price computation and order creation."""
from decimal import Decimal
from ..extensions import db
from ..models.item import Item
from ..models.order import Order
from ..models.order_item import OrderItem


def compute_order_total(cart: dict) -> tuple[Decimal, list[dict]]:
    """
    Re-fetch prices from DB. Never trust client-sent totals.
    cart: {item_id: quantity}
    Returns (total, [validated line items])
    """
    total = Decimal("0.00")
    lines = []
    for item_id_str, qty in cart.items():
        item_id = int(item_id_str)
        qty = int(qty)
        if qty <= 0:
            continue
        item = Item.query.with_entities(
            Item.id, Item.name, Item.price, Item.stock_quantity, Item.is_active
        ).filter_by(id=item_id).first()
        if not item or not item.is_active:
            raise ValueError(f"Item {item_id} is not available.")
        if qty > item.stock_quantity:
            raise ValueError(f"Insufficient stock for '{item.name}'. Available: {item.stock_quantity}.")
        subtotal = item.price * qty
        total += subtotal
        lines.append({
            "item_id": item.id,
            "name": item.name,
            "price": item.price,
            "quantity": qty,
            "subtotal": subtotal,
        })
    if not lines:
        raise ValueError("Cart is empty.")
    return total, lines


def create_order(user_id: int, cart: dict) -> Order:
    """Create an Order and its OrderItems from validated cart data."""
    total, lines = compute_order_total(cart)
    order = Order(user_id=user_id, total_amount=total, status="pending")
    db.session.add(order)
    db.session.flush()  # get order.id before commit

    for line in lines:
        oi = OrderItem(
            order_id=order.id,
            item_id=line["item_id"],
            quantity=line["quantity"],
            price_at_purchase=line["price"],
        )
        db.session.add(oi)

    db.session.commit()
    return order
