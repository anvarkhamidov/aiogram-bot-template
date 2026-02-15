import hashlib
import hmac
import json
from urllib.parse import parse_qsl, unquote

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.cart import CartService
from app.services.order import OrderService
from app.services.restaurant import RestaurantService
from app.services.user import UserService


def validate_webapp_data(init_data: str, bot_token: str) -> dict | None:
    """Validate Telegram WebApp initData and return parsed data."""
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        return None

    user_data = parsed.get("user")
    if user_data:
        parsed["user"] = json.loads(unquote(user_data))
    return parsed


def create_webapp_routes(session_factory: async_sessionmaker[AsyncSession], bot_token: str):
    routes = web.RouteTableDef()

    def _get_user_id(request: web.Request) -> int | None:
        init_data = request.headers.get("X-Telegram-Init-Data", "")
        if not init_data:
            return None
        parsed = validate_webapp_data(init_data, bot_token)
        if parsed and "user" in parsed:
            return parsed["user"].get("id")
        return None

    @routes.get("/api/restaurants")
    async def get_restaurants(request: web.Request) -> web.Response:
        async with session_factory() as session:
            service = RestaurantService(session)
            restaurants = await service.get_all_active()
            return web.json_response([
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "address": r.address,
                    "image_url": r.image_url,
                }
                for r in restaurants
            ])

    @routes.get("/api/restaurants/{restaurant_id}/menu")
    async def get_menu(request: web.Request) -> web.Response:
        restaurant_id = int(request.match_info["restaurant_id"])
        async with session_factory() as session:
            service = RestaurantService(session)
            categories = await service.get_menu(restaurant_id)
            return web.json_response([
                {
                    "id": cat.id,
                    "name": cat.name,
                    "products": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "description": p.description,
                            "price": p.price,
                            "price_display": p.price_display,
                            "image_url": p.image_url,
                            "is_available": p.is_available,
                        }
                        for p in cat.products
                    ],
                }
                for cat in categories
            ])

    @routes.post("/api/cart/add")
    async def add_to_cart(request: web.Request) -> web.Response:
        telegram_id = _get_user_id(request)
        if not telegram_id:
            return web.json_response({"error": "Unauthorized"}, status=401)

        data = await request.json()
        product_id = data.get("product_id")
        quantity = data.get("quantity", 1)

        if not product_id:
            return web.json_response({"error": "product_id required"}, status=400)

        async with session_factory() as session:
            user_service = UserService(session)
            user = await user_service.get_by_telegram_id(telegram_id)
            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            cart_service = CartService(session)
            item = await cart_service.add_item(user.id, product_id, quantity)
            return web.json_response({
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
            })

    @routes.get("/api/cart")
    async def get_cart(request: web.Request) -> web.Response:
        telegram_id = _get_user_id(request)
        if not telegram_id:
            return web.json_response({"error": "Unauthorized"}, status=401)

        async with session_factory() as session:
            user_service = UserService(session)
            user = await user_service.get_by_telegram_id(telegram_id)
            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            cart_service = CartService(session)
            items = await cart_service.get_items(user.id)
            total = sum(item.subtotal for item in items)

            return web.json_response({
                "items": [
                    {
                        "id": item.id,
                        "product_name": item.product.name,
                        "product_price": item.product.price,
                        "quantity": item.quantity,
                        "subtotal": item.subtotal,
                    }
                    for item in items
                ],
                "total": total,
            })

    @routes.delete("/api/cart/{item_id}")
    async def remove_from_cart(request: web.Request) -> web.Response:
        telegram_id = _get_user_id(request)
        if not telegram_id:
            return web.json_response({"error": "Unauthorized"}, status=401)

        item_id = int(request.match_info["item_id"])
        async with session_factory() as session:
            cart_service = CartService(session)
            removed = await cart_service.remove_item(item_id)
            if removed:
                return web.json_response({"ok": True})
            return web.json_response({"error": "Item not found"}, status=404)

    @routes.post("/api/orders")
    async def create_order(request: web.Request) -> web.Response:
        telegram_id = _get_user_id(request)
        if not telegram_id:
            return web.json_response({"error": "Unauthorized"}, status=401)

        data = await request.json()
        address = data.get("address")
        phone = data.get("phone")

        if not address or not phone:
            return web.json_response({"error": "address and phone required"}, status=400)

        async with session_factory() as session:
            user_service = UserService(session)
            user = await user_service.get_by_telegram_id(telegram_id)
            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            cart_service = CartService(session)
            items = await cart_service.get_items(user.id)
            if not items:
                return web.json_response({"error": "Cart is empty"}, status=400)

            restaurant_id = items[0].product.category.restaurant_id

            order_service = OrderService(session)
            order = await order_service.create_from_cart(
                user_id=user.id,
                restaurant_id=restaurant_id,
                cart_items=items,
                delivery_address=address,
                phone=phone,
                comment=data.get("comment"),
            )
            await cart_service.clear(user.id)

            await user_service.update_contact(telegram_id, phone, address)

            return web.json_response({
                "id": order.id,
                "status": order.status.value,
                "total": order.total,
            })

    @routes.get("/api/orders")
    async def get_orders(request: web.Request) -> web.Response:
        telegram_id = _get_user_id(request)
        if not telegram_id:
            return web.json_response({"error": "Unauthorized"}, status=401)

        async with session_factory() as session:
            user_service = UserService(session)
            user = await user_service.get_by_telegram_id(telegram_id)
            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            order_service = OrderService(session)
            orders = await order_service.get_user_orders(user.id)

            return web.json_response([
                {
                    "id": o.id,
                    "status": o.status.value,
                    "total": o.total,
                    "total_display": o.total_display,
                    "address": o.delivery_address,
                    "created_at": o.created_at.isoformat(),
                    "items": [
                        {
                            "name": item.product.name,
                            "quantity": item.quantity,
                            "price": item.price,
                        }
                        for item in o.items
                    ],
                }
                for o in orders
            ])

    @routes.get("/webapp")
    async def webapp_page(request: web.Request) -> web.Response:
        import pathlib

        template_path = pathlib.Path(__file__).parent / "templates" / "index.html"
        return web.FileResponse(template_path, headers={"Content-Type": "text/html"})

    @routes.get("/webapp/static/{filename:.*}")
    async def static_files(request: web.Request) -> web.Response:
        import pathlib

        filename = request.match_info["filename"]
        file_path = pathlib.Path(__file__).parent / "templates" / "static" / filename
        if not file_path.exists():
            return web.Response(status=404)

        content_types = {
            ".css": "text/css",
            ".js": "application/javascript",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml",
        }
        ext = file_path.suffix.lower()
        content_type = content_types.get(ext, "application/octet-stream")
        return web.FileResponse(file_path, headers={"Content-Type": content_type})

    return routes
