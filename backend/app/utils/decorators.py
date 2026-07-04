"""Access control decorators."""
from functools import wraps
from flask import abort, jsonify
from flask_login import current_user


def admin_required(f):
    """Protect a view — only admin users can access it."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated


def owner_required(get_resource_user_id):
    """
    Protect a view so only the owning user (or admin) can access it.
    get_resource_user_id: callable taking **kwargs, returns the owner's user_id.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            owner_id = get_resource_user_id(**kwargs)
            if current_user.role != "admin" and current_user.id != owner_id:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator
