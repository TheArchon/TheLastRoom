import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "").strip()
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017").strip()
    MONGO_DB = os.getenv("MONGO_DB", "last_room").strip()
    SESSION_NAME = os.getenv("SESSION_NAME", "last_room_bot").strip()
    SESSION_DIR = os.getenv("SESSION_DIR", "./sessions").strip()
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip()
    LOBBY_MIN = 4
    LOBBY_MAX = 10
    ROUND_SECONDS = int(os.getenv("ROUND_SECONDS", "90"))
    VOTE_SECONDS = int(os.getenv("VOTE_SECONDS", "60"))

    @classmethod
    def validate(cls):
        missing = []
        if not cls.BOT_TOKEN: missing.append("BOT_TOKEN")
        if not cls.API_ID: missing.append("API_ID")
        if not cls.API_HASH: missing.append("API_HASH")
        if not cls.MONGO_URI: missing.append("MONGO_URI")
        if missing:
            raise RuntimeError("Missing required environment variables: " + ", ".join(missing))
        Path(cls.SESSION_DIR).mkdir(parents=True, exist_ok=True)

Config.validate()
