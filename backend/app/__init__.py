"""Flask application factory."""
import os
import click
from flask import Flask
from .config import config_by_name
from .extensions import db, migrate, login_manager, csrf, limiter
from .models import user, category, item, advertisement, ambience, order, order_item, payment  # noqa: F401
from .utils.errors import register_error_handlers


def create_app(config_name: str | None = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_dir = os.path.join(os.path.dirname(base_dir), "frontend")

    app = Flask(
        __name__,
        template_folder=os.path.join(frontend_dir, "templates"),
        static_folder=os.path.join(frontend_dir, "static"),
    )
    app.config.from_object(config_by_name[config_name])

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Talisman (security headers) — only in production
    if config_name == "production":
        from flask_talisman import Talisman
        Talisman(
            app,
            content_security_policy={
                "default-src": "'self'",
                "script-src": ["'self'", "cdn.jsdelivr.net", "checkout.razorpay.com", "cdnjs.cloudflare.com", "'unsafe-inline'"],
                "style-src": ["'self'", "fonts.googleapis.com", "cdn.jsdelivr.net", "'unsafe-inline'"],
                "font-src": ["'self'", "fonts.gstatic.com"],
                "img-src": ["'self'", "data:"],
                "frame-src": ["api.razorpay.com", "www.google.com"],
            },
            force_https=False,           # Vercel enforces HTTPS at the edge
            strict_transport_security=True,
        )

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.items import items_bp
    from .routes.admin import admin_bp
    from .routes.cart import cart_bp
    from .routes.orders import orders_bp
    from .routes.payments import payments_bp
    from .routes.ads import ads_bp
    from .routes.ambience import ambience_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(items_bp, url_prefix="/items")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(orders_bp, url_prefix="/orders")
    app.register_blueprint(payments_bp, url_prefix="/payments")
    app.register_blueprint(ads_bp, url_prefix="/ads")
    app.register_blueprint(ambience_bp, url_prefix="/ambience")

    register_error_handlers(app)

    # ── Jinja2 globals — available in every template ──────────────────────
    from datetime import date as _date, datetime as _datetime
    app.jinja_env.globals["now"] = _datetime.utcnow
    app.jinja_env.globals["today"] = _date.today

    @app.context_processor
    def inject_globals():
        from datetime import date as _d, datetime as _dt
        return {
            "now": _dt.utcnow(),
            "today": _d.today().isoformat(),
        }

    # Public index route
    from flask import render_template
    from flask_login import login_required as _lr
    from .models.advertisement import Advertisement
    from .models.item import Item
    from .models.category import Category
    from datetime import date

    @app.route("/")
    def index():
        from .repositories import AdRepo, CategoryRepo, ItemRepo
        from .services.cache_service import (
            get_cached_ads, set_cached_ads,
            get_cached_categories, set_cached_categories,
            get_cached_featured, set_cached_featured,
        )

        # ── Ads ───────────────────────────────────────────────────────────
        ads = get_cached_ads()
        if ads is None:
            ads = AdRepo.active_today()
            set_cached_ads(ads)

        # ── Categories ────────────────────────────────────────────────────
        categories = get_cached_categories()
        if categories is None:
            categories = CategoryRepo.all()
            set_cached_categories(categories)

        # ── Featured items ────────────────────────────────────────────────
        featured = get_cached_featured()
        if featured is None:
            featured = ItemRepo.featured(limit=8)
            set_cached_featured(featured)

        return render_template("index.html", ads=ads, categories=categories, featured=featured)

    @app.route("/checkout")
    @_lr
    def checkout():
        from .routes.cart import get_cart
        from .models.item import Item
        cart = get_cart()
        items_in_cart = []
        total = 0
        for item_id_str, qty in cart.items():
            item = Item.query.filter_by(id=int(item_id_str), is_active=True).first()
            if item:
                subtotal = float(item.price) * qty
                total += subtotal
                items_in_cart.append({"item": item, "qty": qty, "subtotal": subtotal})
        if not items_in_cart:
            from flask import redirect, url_for, flash
            flash("Your cart is empty.", "warning")
            return redirect(url_for("cart.view_cart"))
        return render_template("checkout.html", cart_items=items_in_cart, total=total)

    # CLI: create admin
    @app.cli.command("create-admin")
    @click.option("--email", default=None, help="Admin email")
    @click.option("--password", default=None, help="Admin password")
    def create_admin(email, password):
        """Seed the admin user. Never registerable through public form."""
        from .models.user import User
        import bcrypt as _bcrypt

        email = email or app.config["ADMIN_SEED_EMAIL"]
        password = password or app.config["ADMIN_SEED_PASSWORD"]

        if not email or not password:
            click.echo("Provide email and password via options or .env ADMIN_SEED_EMAIL / ADMIN_SEED_PASSWORD")
            return

        existing = User.query.filter_by(email=email).first()
        if existing:
            click.echo(f"Admin user {email} already exists.")
            return

        pw_hash = _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt(rounds=12))
        admin = User(
            name="Admin",
            email=email,
            password_hash=pw_hash.decode("utf-8"),
            role="admin",
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Admin user {email} created successfully.")

    return app
