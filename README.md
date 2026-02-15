# Food Delivery Bot

Telegram WebApp bot for ordering food from restaurants.

## Features

- Browse restaurants, categories, and dishes
- Add items to cart, checkout with delivery address and phone
- Order lifecycle: pending -> confirmed -> preparing -> delivering -> delivered
- Telegram Mini App (WebApp) with responsive UI
- Admin panel for order management
- Full test suite (80 tests)

## Quick Start

### 1. Get a Bot Token

Create a bot via [@BotFather](https://t.me/BotFather) and copy the token.

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set your BOT_BOT_TOKEN
```

### 3. Install dependencies

```bash
pip install -e ".[dev]"
```

### 4. Run the bot

```bash
python -m app.main
```

Or run just the WebApp demo server with sample data:

```bash
python dev_server.py
# Open http://localhost:8080/webapp
```

### 5. Seed sample data

In Telegram, send `/seed` to your bot (you must be in the `BOT_ADMIN_IDS` list).

## Docker

```bash
cp .env.example .env
# Edit .env
docker compose up -d
```

## Bot Commands

| Command   | Description                    |
|-----------|--------------------------------|
| `/start`  | Register and see welcome       |
| `/menu`   | Browse restaurants             |
| `/cart`   | View cart and checkout         |
| `/orders` | Order history                  |
| `/webapp` | Open Mini App                  |
| `/admin`  | Admin panel (admin only)       |
| `/pending`| View pending orders (admin)    |
| `/seed`   | Load sample data (admin)       |

## Running Tests

```bash
pytest -v
```

## Project Structure

```
app/
├── models/       # SQLAlchemy 2.0 async models
├── services/     # Business logic layer
├── handlers/     # aiogram 3.x message/callback handlers
├── keyboards/    # Inline keyboards + WebApp button
├── webapp/       # Telegram Mini App (aiohttp API + HTML/CSS/JS)
├── middlewares/  # DB session middleware
├── config.py     # pydantic-settings configuration
└── main.py       # Entry point
database/         # Engine and session factory
tests/            # 80 tests (models, services, keyboards, webapp, middleware)
```

## WebApp (Mini App)

The Mini App provides a rich mobile UI for browsing restaurants, viewing menus, managing cart, and placing orders. It uses Telegram theme variables for native look and feel.

To use the Mini App, set `BOT_WEBAPP_BASE_URL` to your public HTTPS domain where the bot is hosted.
