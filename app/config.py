import json

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str = ""
    database_url: str = "sqlite+aiosqlite:///data/food_delivery.db"
    webapp_base_url: str = "https://example.com"
    webapp_host: str = "0.0.0.0"
    webapp_port: int = 8080
    admin_ids: list[int] = []
    webhook_path: str = "/webhook"
    webhook_secret: str = ""

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        return v

    model_config = {"env_prefix": "BOT_", "env_file": ".env"}


settings = Settings()
