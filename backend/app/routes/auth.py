"""Authentication routes — register, login, logout."""
import bcrypt
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from ..extensions import db, limiter
from ..models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        phone = request.form.get("phone", "").strip()

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("auth/register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("Invalid credentials.", "danger")  # Don't reveal email exists
            return render_template("auth/register.html")

        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
        user = User(name=name, email=email, password_hash=pw_hash.decode("utf-8"), phone=phone)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welcome to Viraamam! Your account has been created.", "success")
        return redirect(url_for("index"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes", methods=["POST"], error_message="Too many login attempts. Please wait 15 minutes.")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember", False)

        user = User.query.filter_by(email=email).first()
        if not user or not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            flash("Invalid credentials.", "danger")
            return render_template("auth/login.html")

        if not user.is_active:
            flash("Invalid credentials.", "danger")
            return render_template("auth/login.html")

        login_user(user, remember=bool(remember))
        next_page = request.args.get("next")
        flash(f"Welcome back, {user.name}!", "success")

        if user.is_admin:
            return redirect(next_page or url_for("admin.dashboard"))
        return redirect(next_page or url_for("index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))
