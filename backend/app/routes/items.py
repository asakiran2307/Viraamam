"""Public item routes — catalog, detail, and image serving via Repository pattern."""
import hashlib
from flask import Blueprint, render_template, request, abort, Response, make_response
from ..repositories import ItemRepo, CategoryRepo
from ..services.cache_service import (
    get_cached_catalog, set_cached_catalog,
    get_cached_categories, set_cached_categories,
    get_cached_item, set_cached_item,
)

items_bp = Blueprint("items", __name__)
PER_PAGE = 12


@items_bp.route("/")
def catalog():
    page = request.args.get("page", 1, type=int)
    category_slug = request.args.get("category", "").strip()
    search = request.args.get("q", "").strip()

    # ── 1. Try Redis cache ────────────────────────────────────────────────────
    cached = get_cached_catalog(page, category_slug, search)
    if cached:
        return render_template(
            "menu.html",
            items=cached["items"],
            pagination=cached["pagination"],
            categories=cached["categories"],
            current_category=category_slug,
            search=search,
        )

    # ── 2. Cache miss → Repository query ──────────────────────────────────────
    category_id = None
    if category_slug:
        cat = CategoryRepo.get_by_slug(category_slug)
        if cat:
            category_id = cat.id

    pagination = ItemRepo.list_active(
        category_id=category_id,
        search=search,
        page=page,
        per_page=PER_PAGE,
    )

    categories = get_cached_categories()
    if categories is None:
        categories = CategoryRepo.all()
        set_cached_categories(categories)

    # ── 3. Store in cache ─────────────────────────────────────────────────────
    set_cached_catalog(page, category_slug, search, {
        "items": pagination.items,
        "pagination": pagination,
        "categories": categories,
    })

    return render_template(
        "menu.html",
        items=pagination.items,
        pagination=pagination,
        categories=categories,
        current_category=category_slug,
        search=search,
    )


@items_bp.route("/<int:item_id>")
def detail(item_id: int):
    item = get_cached_item(item_id)
    if item is None:
        item = ItemRepo.get_active_by_id(item_id)
        if item is None:
            abort(404)
        set_cached_item(item_id, item)
    elif not item.is_active:
        abort(404)
    return render_template("item_detail.html", item=item)


@items_bp.route("/<int:item_id>/image")
def image(item_id: int):
    """Serve item image from DB — uses ETag for browser caching (no redundant downloads)."""
    row = ItemRepo.get_image(item_id)
    if not row or not row.image_data:
        abort(404)

    etag = hashlib.md5(row.image_data[:64]).hexdigest()
    if request.headers.get("If-None-Match") == etag:
        return Response(status=304)

    resp = make_response(row.image_data)
    resp.headers["Content-Type"] = row.image_mime_type or "image/jpeg"
    resp.headers["Cache-Control"] = "public, max-age=86400"
    resp.headers["ETag"] = etag
    return resp
