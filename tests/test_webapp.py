import json

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, TestClient, TestServer

from app.models.category import Category
from app.models.product import Product
from app.models.restaurant import Restaurant
from app.models.user import User
from app.webapp.routes import create_webapp_routes, validate_webapp_data


class TestValidateWebappData:
    def test_validate_missing_hash(self):
        result = validate_webapp_data("user=test&auth_date=123", "token")
        assert result is None

    def test_validate_invalid_hash(self):
        result = validate_webapp_data("user=test&auth_date=123&hash=invalid", "token")
        assert result is None


@pytest.fixture
async def webapp_client(session_factory):
    """Create aiohttp test client with webapp routes."""
    app = web.Application()
    routes = create_webapp_routes(session_factory, "test_token")
    app.router.add_routes(routes)

    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()
    yield client
    await client.close()


@pytest.fixture
async def seeded_db(session):
    """Seed the database with test data."""
    user = User(telegram_id=12345, first_name="TestUser")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    restaurant = Restaurant(name="Test Restaurant", description="A test place", is_active=True)
    session.add(restaurant)
    await session.commit()
    await session.refresh(restaurant)

    category = Category(name="Mains", restaurant_id=restaurant.id)
    session.add(category)
    await session.commit()
    await session.refresh(category)

    product = Product(
        name="Burger", price=999, category_id=category.id, description="Tasty burger"
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)

    return {
        "user": user,
        "restaurant": restaurant,
        "category": category,
        "product": product,
    }


async def test_get_restaurants(webapp_client, seeded_db):
    resp = await webapp_client.get("/api/restaurants")
    assert resp.status == 200
    data = await resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Restaurant"


async def test_get_restaurants_empty(webapp_client):
    resp = await webapp_client.get("/api/restaurants")
    assert resp.status == 200
    data = await resp.json()
    assert data == []


async def test_get_menu(webapp_client, seeded_db):
    rid = seeded_db["restaurant"].id
    resp = await webapp_client.get(f"/api/restaurants/{rid}/menu")
    assert resp.status == 200
    data = await resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Mains"
    assert len(data[0]["products"]) == 1
    assert data[0]["products"][0]["name"] == "Burger"


async def test_add_to_cart_unauthorized(webapp_client, seeded_db):
    resp = await webapp_client.post(
        "/api/cart/add",
        json={"product_id": seeded_db["product"].id},
    )
    assert resp.status == 401


async def test_get_cart_unauthorized(webapp_client):
    resp = await webapp_client.get("/api/cart")
    assert resp.status == 401


async def test_create_order_unauthorized(webapp_client):
    resp = await webapp_client.post(
        "/api/orders",
        json={"address": "Test", "phone": "123"},
    )
    assert resp.status == 401


async def test_get_orders_unauthorized(webapp_client):
    resp = await webapp_client.get("/api/orders")
    assert resp.status == 401


async def test_webapp_page(webapp_client):
    resp = await webapp_client.get("/webapp")
    assert resp.status == 200
    text = await resp.text()
    assert "Food Delivery" in text


async def test_static_css(webapp_client):
    resp = await webapp_client.get("/webapp/static/css/style.css")
    assert resp.status == 200


async def test_static_js(webapp_client):
    resp = await webapp_client.get("/webapp/static/js/app.js")
    assert resp.status == 200


async def test_static_not_found(webapp_client):
    resp = await webapp_client.get("/webapp/static/nonexistent.js")
    assert resp.status == 404
