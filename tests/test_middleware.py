from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.middlewares.db import DbSessionMiddleware


async def test_db_session_middleware(session_factory):
    middleware = DbSessionMiddleware(session_factory)

    handler = AsyncMock(return_value="result")
    event = MagicMock()
    data = {}

    result = await middleware(handler, event, data)

    assert result == "result"
    assert "session" in data
    assert isinstance(data["session"], AsyncSession)
    handler.assert_awaited_once()
