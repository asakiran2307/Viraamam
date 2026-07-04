"""Admin routes — protected CRUD via Repository pattern (SQLAlchemy 2.0).

All DB access goes through repositories.py — no Model.query calls here.
"""
import hashlib
from datetime import date, datetime
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, abort, Response, make_response, jsonify)
from flask_login import login_required, current_user
from ..extensions import db
from ..models.item import Item
from ..models.category import Category
from ..models.advertisement import Advertisement
from ..models.ambience import AmbiencePhoto
from ..repositories import ItemRepo, CategoryRepo, OrderRepo, AdRepo, AmbienceRepo
from ..services.image_service import process_uploaded_image
from ..services.cache_service import invalidate_catalog_cache, invalidate_item_cache
from ..utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__)


# ─── Dashboard ─────────────────────────────────────────────────────────────

@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    return render_template(
        "admin/dashboard.html",
        today_orders=OrderRepo.count_today(),
        today_revenue=OrderRepo.revenue_today(),
        low_stock=ItemRepo.count_low_stock(),
        out_of_stock=ItemRepo.count_out_of_stock(),
        total_items=ItemRepo.count_active(),
        recent_orders=OrderRepo.recent(limit=10),
    )


# ─── Categories ────────────────────────────────────────────────────────────

@admin_bp.route("/categories", methods=["GET", "POST"])
@login_required
@admin_required
def categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip().lower().replace(" ", "-")
        if not name or not slug:
            flash("Name and slug are required.", "danger")
        elif CategoryRepo.slug_exists(slug):
            flash("Slug already exists.", "danger")
        else:
            db.session.add(Category(name=name, slug=slug))
            db.session.commit()
            invalidate_catalog_cache()
            flash(f"Category '{name}' created.", "success")
        return redirect(url_for("admin.categories"))

    return render_template("admin/categories.html", categories=CategoryRepo.all())


@admin_bp.route("/categories/<int:cat_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_category(cat_id: int):
    cat = CategoryRepo.get_by_id(cat_id)
    if not cat:
        abort(404)
    db.session.delete(cat)
    db.session.commit()
    invalidate_catalog_cache()
    flash(f"Category '{cat.name}' deleted.", "info")
    return redirect(url_for("admin.categories"))


# ─── Items ─────────────────────────────────────────────────────────────────

@admin_bp.route("/items")
@login_required
@admin_required
def items():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "").strip()
    pagination = ItemRepo.list_all_admin(search=search, page=page, per_page=20)
    return render_template(
        "admin/items.html",
        items=pagination.items,
        pagination=pagination,
        search=search,
    )


@admin_bp.route("/items/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_item():
    categories = CategoryRepo.all()
    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            description = request.form.get("description", "").strip()
            price = float(request.form.get("price", 0))
            stock = int(request.form.get("stock_quantity", 0))
            category_id_raw = request.form.get("category_id")
            category_id = int(category_id_raw) if category_id_raw and category_id_raw.strip() else None
            is_active = bool(request.form.get("is_active"))

            item = Item(
                name=name, description=description,
                price=price, stock_quantity=stock,
                category_id=category_id, is_active=is_active,
            )
            image_file = request.files.get("image")
            if image_file and image_file.filename:
                img_bytes, mime = process_uploaded_image(image_file)
                item.image_data = img_bytes
                item.image_mime_type = mime

            db.session.add(item)
            db.session.commit()
            invalidate_catalog_cache()
            flash(f"Item '{name}' added successfully.", "success")
            return redirect(url_for("admin.items"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("admin/add_edit_item.html", item=None, categories=categories, action="Add")


@admin_bp.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_item(item_id: int):
    item = ItemRepo.get_by_id(item_id)
    if not item:
        abort(404)
    categories = CategoryRepo.all()
    if request.method == "POST":
        try:
            item.name = request.form.get("name", "").strip()
            item.description = request.form.get("description", "").strip()
            item.price = float(request.form.get("price", 0))
            item.stock_quantity = int(request.form.get("stock_quantity", 0))
            category_id_raw = request.form.get("category_id")
            item.category_id = int(category_id_raw) if category_id_raw and category_id_raw.strip() else None
            item.is_active = bool(request.form.get("is_active"))

            image_file = request.files.get("image")
            if image_file and image_file.filename:
                img_bytes, mime = process_uploaded_image(image_file)
                item.image_data = img_bytes
                item.image_mime_type = mime

            db.session.commit()
            invalidate_item_cache(item_id)
            flash(f"Item '{item.name}' updated.", "success")
            return redirect(url_for("admin.items"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("admin/add_edit_item.html", item=item, categories=categories, action="Edit")


@admin_bp.route("/items/<int:item_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_item(item_id: int):
    item = ItemRepo.get_by_id(item_id)
    if not item:
        abort(404)
    item.is_active = False   # Soft delete — preserves order history
    db.session.commit()
    invalidate_item_cache(item_id)
    flash(f"Item '{item.name}' deactivated.", "info")
    return redirect(url_for("admin.items"))


@admin_bp.route("/items/<int:item_id>/image")
@login_required
@admin_required
def item_image(item_id: int):
    row = ItemRepo.get_image(item_id)
    if not row or not row.image_data:
        abort(404)
    resp = make_response(row.image_data)
    resp.headers["Content-Type"] = row.image_mime_type or "image/jpeg"
    return resp


# ─── Advertisements ────────────────────────────────────────────────────────

@admin_bp.route("/advertisements")
@login_required
@admin_required
def advertisements():
    return render_template(
        "admin/advertisements.html",
        ads=AdRepo.all_admin(),
        items=ItemRepo.featured(limit=100),  # all active items for dropdown
    )


@admin_bp.route("/advertisements/add", methods=["POST"])
@login_required
@admin_required
def add_advertisement():
    try:
        title = request.form.get("title", "").strip()
        display_order = int(request.form.get("display_order", 0))
        start_date = date.fromisoformat(request.form.get("start_date") or str(date.today()))
        end_date = date.fromisoformat(request.form.get("end_date") or "2099-12-31")
        item_id_raw = request.form.get("item_id")
        item_id = int(item_id_raw) if item_id_raw and item_id_raw.strip() else None
        is_active = bool(request.form.get("is_active"))

        ad = Advertisement(
            title=title, display_order=display_order,
            start_date=start_date, end_date=end_date,
            item_id=item_id, is_active=is_active,
        )
        image_file = request.files.get("image")
        if image_file and image_file.filename:
            img_bytes, mime = process_uploaded_image(image_file)
            ad.image_data = img_bytes
            ad.image_mime_type = mime

        db.session.add(ad)
        db.session.commit()
        flash("Advertisement added.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.advertisements"))


@admin_bp.route("/advertisements/<int:ad_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_advertisement(ad_id: int):
    ad = AdRepo.get_by_id(ad_id)
    if not ad:
        abort(404)
    ad.is_active = not ad.is_active
    db.session.commit()
    return jsonify(success=True, is_active=ad.is_active)


@admin_bp.route("/advertisements/<int:ad_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_advertisement(ad_id: int):
    ad = AdRepo.get_by_id(ad_id)
    if not ad:
        abort(404)
    db.session.delete(ad)
    db.session.commit()
    flash("Advertisement deleted.", "info")
    return redirect(url_for("admin.advertisements"))


@admin_bp.route("/advertisements/<int:ad_id>/image")
@login_required
@admin_required
def ad_image(ad_id: int):
    ad = AdRepo.get_by_id(ad_id)
    if not ad or not ad.image_data:
        abort(404)
    resp = make_response(ad.image_data)
    resp.headers["Content-Type"] = ad.image_mime_type or "image/jpeg"
    return resp


# ─── Ambience Photos ───────────────────────────────────────────────────────

@admin_bp.route("/ambience")
@login_required
@admin_required
def ambience_admin():
    return render_template("admin/ambience_admin.html", photos=AmbienceRepo.all_admin())


@admin_bp.route("/ambience/upload", methods=["POST"])
@login_required
@admin_required
def upload_ambience():
    try:
        title = request.form.get("title", "").strip() or "Untitled"
        caption = request.form.get("caption", "").strip()
        display_order = int(request.form.get("display_order", 0))
        is_active = bool(request.form.get("is_active", True))

        image_file = request.files.get("image")
        if not image_file or not image_file.filename:
            flash("Please select an image to upload.", "danger")
            return redirect(url_for("admin.ambience_admin"))

        img_bytes, mime = process_uploaded_image(image_file)
        photo = AmbiencePhoto(
            title=title, caption=caption,
            image_data=img_bytes, image_mime_type=mime,
            display_order=display_order, is_active=is_active,
        )
        db.session.add(photo)
        db.session.commit()
        flash(f"Photo '{title}' uploaded successfully.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin.ambience_admin"))


@admin_bp.route("/ambience/<int:photo_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_ambience(photo_id: int):
    photo = AmbienceRepo.get_by_id(photo_id)
    if not photo:
        abort(404)
    photo.is_active = not photo.is_active
    db.session.commit()
    return jsonify(success=True, is_active=photo.is_active)


@admin_bp.route("/ambience/<int:photo_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_ambience(photo_id: int):
    photo = AmbienceRepo.get_by_id(photo_id)
    if not photo:
        abort(404)
    db.session.delete(photo)
    db.session.commit()
    flash("Photo deleted.", "info")
    return redirect(url_for("admin.ambience_admin"))


@admin_bp.route("/ambience/<int:photo_id>/image")
@login_required
@admin_required
def ambience_photo_image(photo_id: int):
    photo = AmbienceRepo.get_by_id(photo_id)
    if not photo or not photo.image_data:
        abort(404)
    resp = make_response(photo.image_data)
    resp.headers["Content-Type"] = photo.image_mime_type or "image/jpeg"
    return resp


# ─── Orders ───────────────────────────────────────────────────────────────

@admin_bp.route("/orders")
@login_required
@admin_required
def orders():
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "").strip() or None
    pagination = OrderRepo.all_admin(page=page, per_page=20, status=status)
    return render_template(
        "admin/orders.html",
        orders=pagination.items,
        pagination=pagination,
        current_status=status or "",
    )


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
@admin_required
def update_order_status(order_id: int):
    order = OrderRepo.get_by_id(order_id)
    if not order:
        abort(404)
    new_status = request.form.get("status")
    valid = ["pending", "paid", "preparing", "completed", "cancelled"]
    if new_status not in valid:
        flash("Invalid status.", "danger")
    else:
        OrderRepo.update_status(order_id, new_status)
        db.session.commit()
        flash(f"Order #{order_id} updated to '{new_status}'.", "success")
    return redirect(url_for("admin.orders"))
