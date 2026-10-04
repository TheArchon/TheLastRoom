import asyncio
import logging

from pyrogram import Client

from config import Config
from database import Database
from game.engine import GameEngine
from handlers.commands import register_command_handlers
from handlers.callbacks import register_callback_handlers
from services.scheduler import GameScheduler


logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("last_room")


class LastRoomBot:
    def __init__(self):
        self.app = Client(
            name=Config.SESSION_NAME,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workdir=Config.SESSION_DIR,
        )
        self.db = Database(Config.MONGO_URI, Config.MONGO_DB)
        self.engine = GameEngine(self.app, self.db)
        self.scheduler = GameScheduler(self.engine)
        register_command_handlers(self.app, self.engine)
        register_callback_handlers(self.app, self.engine)

    async def start(self):
        await self.db.connect()
        await self.db.ensure_indexes()
        await self.app.start()
        me = await self.app.get_me()
        log.info("Bot started as @%s", me.username)
        await self.scheduler.start()

    async def stop(self):
        await self.scheduler.stop()
        await self.db.close()
        await self.app.stop()

    async def run(self):
        await self.start()
        try:
            await asyncio.Event().wait()
        finally:
            await self.stop()


if __name__ == "__main__":
    asyncio.run(LastRoomBot().run())
