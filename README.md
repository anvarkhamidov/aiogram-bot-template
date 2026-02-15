# Food Delivery Bot

Telegram WebApp bot for ordering food from restaurants.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/anvarkhamidov/aiogram-bot-template)

## Features

- Browse restaurants, categories, and dishes
- Add items to cart, checkout with delivery address and phone
- Order lifecycle: pending -> confirmed -> preparing -> delivering -> delivered
- Telegram Mini App (WebApp) with responsive UI
- Admin panel for order management
- Full test suite (80 tests)

## Deploy for Free (Render.com)

The fastest way to get the bot running:

1. Fork this repo on GitHub
2. Go to [render.com](https://render.com) and sign up (free)
3. Click **New > Blueprint** and connect your forked repo
4. Set environment variables:
   - `BOT_BOT_TOKEN` — your token from [@BotFather](https://t.me/BotFather)
   - `BOT_WEBAPP_BASE_URL` — will be `https://food-delivery-bot.onrender.com` (your Render URL)
   - `BOT_ADMIN_IDS` — your Telegram user ID, e.g. `[123456789]`
5. Click **Deploy** — done!

The bot will auto-seed sample restaurants on first launch.

## Quick Start (Local)

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
python start.py
```

Or run just the WebApp demo server with sample data:

```bash
python dev_server.py
# Open http://localhost:8080/webapp
```

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
