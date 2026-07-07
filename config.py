import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _str_to_bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


class Config:
    """Configuration commune à tous les environnements."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "change-moi")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'academie.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = _str_to_bool(os.environ.get("SQLALCHEMY_ECHO", "False"))


class TestingConfig(Config):
    """Configuration utilisée par la suite de tests : base en mémoire, isolée."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ECHO = False


CONFIG_BY_NAME = {
    "development": Config,
    "testing": TestingConfig,
    "production": Config,
}
