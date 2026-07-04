"""Orders routes."""
from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from ..models.order import Order

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/")
@login_required
def my_orders():
    orders = (Order.query
              .filter_by(user_id=current_user.id)
              .order_by(Order.created_at.desc())
              .all())
    return render_template("orders.html", orders=orders)


@orders_bp.route("/<int:order_id>")
@login_required
def order_detail(order_id: int):
    order = Order.query.filter_by(id=order_id).first_or_404()
    # Ensure only the owner (or admin) can view
    if current_user.role != "admin" and order.user_id != current_user.id:
        abort(403)
    return render_template("order_detail.html", order=order)
