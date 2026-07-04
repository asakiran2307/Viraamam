"""Public ads endpoint."""
from datetime import date
from flask import Blueprint, jsonify
from ..models.advertisement import Advertisement

ads_bp = Blueprint("ads", __name__)


@ads_bp.route("/active")
def active_ads():
    ads = (Advertisement.query
           .filter_by(is_active=True)
           .filter(Advertisement.start_date <= date.today(), Advertisement.end_date >= date.today())
           .order_by(Advertisement.display_order)
           .all())
    return jsonify([{"id": a.id, "title": a.title} for a in ads])
