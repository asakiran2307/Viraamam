# Viraamam Cafe — Full-Stack Ordering Platform

A production-grade cafe ordering platform built with Flask, Neon PostgreSQL, Redis, and Razorpay.

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.12+
- pip
- (Optional) Redis for caching

### 1. Clone and setup

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your values
```

Minimum required for local dev:
```
FLASK_ENV=development
SECRET_KEY=any-random-string
DATABASE_URL=sqlite:///viraamam_dev.db   # SQLite for local dev, no Neon needed
ADMIN_SEED_EMAIL=admin@viraamam.com
ADMIN_SEED_PASSWORD=Admin@1234!
```

### 3. Initialize database

```bash
cd backend
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```

### 4. Create admin user

```bash
flask create-admin
# Or with custom credentials:
flask create-admin --email your@email.com --password YourPassword
```

### 5. Run the development server

```bash
flask run
```

Visit: `http://localhost:5000`

---

## 📁 Project Structure

```
ecomerce/
├── backend/
│   ├── app/
│   │   ├── __init__.py        # App factory
│   │   ├── config.py          # Environment configs
│   │   ├── extensions.py      # SQLAlchemy, Login, CSRF, Limiter
│   │   ├── models/            # Database models
│   │   ├── routes/            # Flask blueprints
│   │   ├── services/          # Business logic
│   │   └── utils/             # Decorators, error handlers
│   ├── migrations/            # Alembic migrations
│   ├── .env.example
│   ├── requirements.txt
│   └── wsgi.py
├── frontend/
│   ├── static/
│   │   ├── css/style.css      # Full design system
│   │   └── js/                # Three.js, Swiper, Cart, Checkout, Ambience
│   └── templates/
│       ├── base.html          # Base layout with navbar & footer
│       ├── index.html         # Homepage (hero + carousel + featured)
│       ├── menu.html          # Full catalog with filters
│       ├── item_detail.html   # Item detail page
│       ├── ambience.html      # 📷 Ambience gallery page
│       ├── checkout.html      # Razorpay checkout
│       ├── cart.html          # Cart page
│       ├── orders.html        # My orders
│       ├── auth/              # Login + Register
│       ├── admin/             # Admin panel templates
│       └── errors/            # 404, 403, 500 pages
├── nginx/nginx.conf
├── docker-compose.yml
└── README.md
```

---

## 🎨 Pages

| Page | URL | Description |
|------|-----|-------------|
| Home | `/` | Hero, carousel, featured items |
| Menu | `/items/` | Full catalog with search & filters |
| Item Detail | `/items/<id>` | Image, price, stock, add to cart |
| **Ambience** | `/ambience/` | **Photo gallery — admin-uploaded** |
| Cart | `/cart/` | Cart page with quantity controls |
| Checkout | `/checkout` | Razorpay payment page |
| My Orders | `/orders/` | Order history |
| Login | `/auth/login` | |
| Register | `/auth/register` | |
| Admin | `/admin/` | Dashboard, items, ads, ambience, orders |

---

## 🖼️ Ambience Page

The **Ambience** page (`/ambience/`) displays a masonry photo gallery showcasing the cafe's interior and atmosphere.

### Admin Upload Flow:
1. Log in as admin → go to `/admin/ambience`
2. Fill in: **Title**, **Caption** (optional), **Display Order**, **Active** toggle
3. Select a photo (JPEG/PNG/WebP, max 5MB)
4. Click **Upload Photo**
5. Photo appears immediately on the public Ambience gallery page

Photos are stored directly in the PostgreSQL database as BYTEA (no file system needed).

---

## 🔐 Security Features

- Bcrypt password hashing (cost factor 12)
- CSRF protection on all forms (Flask-WTF)
- Rate limiting on login (5 attempts/15 min per IP)
- Image validation: Pillow magic bytes check + re-encoding (strips malicious payloads)
- SQL injection prevention: ORM-only queries, no string formatting
- Server-side price/total computation (never trust client)
- Razorpay HMAC signature verification (callback + webhook)
- Atomic stock decrement (`UPDATE WHERE stock >= qty`)
- Role-based access control (`@admin_required` on every admin route)
- Owner check on order endpoints (`order.user_id == current_user.id`)
- HTTP security headers via flask-talisman (production)

---

## 💳 Razorpay Integration

Add to `.env`:
```
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

Configure webhook URL in Razorpay dashboard: `https://yourdomain.com/payments/webhook`
Event: `payment.captured`

---

## 🗄️ Database (Neon PostgreSQL)

1. Create a free Neon account at https://neon.tech
2. Copy the **pooler** connection string (not the direct one)
3. Add to `.env`:
```
DATABASE_URL=postgresql://user:pass@ep-xxxx-pooler.region.aws.neon.tech/dbname?sslmode=require
```

---

## 🐳 Docker Deployment

```bash
# Build and start
docker-compose up -d

# Run migrations inside container
docker-compose exec app flask db upgrade
docker-compose exec app flask create-admin
```

---

## 🔧 Environment Variables

| Variable | Description |
|----------|-------------|
| `FLASK_ENV` | `development` or `production` |
| `SECRET_KEY` | Random 64-char string for sessions |
| `DATABASE_URL` | Neon pooler PostgreSQL URL |
| `REDIS_URL` | Redis connection URL |
| `RAZORPAY_KEY_ID` | Razorpay API key |
| `RAZORPAY_KEY_SECRET` | Razorpay secret |
| `RAZORPAY_WEBHOOK_SECRET` | Webhook signing secret |
| `ADMIN_SEED_EMAIL` | Initial admin email |
| `ADMIN_SEED_PASSWORD` | Initial admin password |
| `MAX_CONTENT_LENGTH_MB` | Max image upload size (default: 5) |

---

*Built for Viraamam Cafe — where every sip tells a story. ☕*
