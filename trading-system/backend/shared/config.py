"""
Loads all configuration from .env and settings.yaml.
Import `settings` and `yaml_config` anywhere in the app.
"""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
import yaml

# Paths
ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"


class Settings(BaseSettings):
    """
    Values are read from backend/config/.env automatically.
    Each field maps to an environment variable of the same name (case-insensitive).
    """
    database_url: str = Field(..., alias="DATABASE_URL")
    mt5_login: int = Field(0, alias="MT5_LOGIN")
    mt5_password: str = Field("", alias="MT5_PASSWORD")
    mt5_server: str = Field("", alias="MT5_SERVER")
    env: str = Field("development", alias="ENV")

    model_config = {
        "env_file": str(CONFIG_DIR / ".env"),
        "populate_by_name": True,
    }


def get_yaml_config() -> dict:
    """Load trading/bot/risk/execution config from settings.yaml."""
    config_path = CONFIG_DIR / "settings.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# Module-level singletons — import these directly
settings = Settings()
yaml_config = get_yaml_config()
