"""Environment-based configuration classes."""
import os
from dotenv import load_dotenv

load_dotenv()


def _fix_db_url(url: str | None) -> str | None:
    """Vercel/Neon returns postgres:// but SQLAlchemy 2.x needs postgresql://"""
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 5)) * 1024 * 1024
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-dev-secret")
    JWT_ACCESS_TOKEN_EXPIRES = 900        # 15 min
    JWT_REFRESH_TOKEN_EXPIRES = 2592000   # 30 days
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
    ADMIN_SEED_EMAIL = os.environ.get("ADMIN_SEED_EMAIL", "admin@viraamam.com")
    ADMIN_SEED_PASSWORD = os.environ.get("ADMIN_SEED_PASSWORD", "Admin@1234!")
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    CAFE_NAME = os.environ.get("CAFE_NAME", "Viraamam")
    # Rate limiter: use memory:// if Redis not configured (safe for serverless)
    RATELIMIT_STORAGE_URI = os.environ.get("REDIS_URL", "memory://")
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _fix_db_url(
        os.environ.get("DATABASE_URL", "sqlite:///viraamam_dev.db")
    )
    SESSION_COOKIE_SECURE = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = _fix_db_url(os.environ.get("DATABASE_URL"))
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Strict"
    # ── Serverless-safe pool: NullPool ────────────────────────────────────────
    # Vercel functions are ephemeral — persistent connection pools cause errors.
    # NullPool opens a fresh connection per request and closes it immediately.
    # Neon's connection pooler (built-in) handles the actual pooling externally.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": __import__("sqlalchemy.pool", fromlist=["NullPool"]).NullPool,
        "pool_pre_ping": True,
        "connect_args": {
            "sslmode": "require",
        },
    }
    # Use memory limiter on serverless (no persistent Redis)
    RATELIMIT_STORAGE_URI = os.environ.get("REDIS_URL", "memory://")


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
