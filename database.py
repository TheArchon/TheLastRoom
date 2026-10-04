from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient


def utcnow():
    return datetime.now(timezone.utc)


class Database:
    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None

    async def connect(self):
        self.client = AsyncIOMotorClient(
            self.uri,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=30,
            minPoolSize=1,
        )
        await self.client.admin.command("ping")
        self.db = self.client[self.db_name]

    async def close(self):
        if self.client:
            self.client.close()

    async def ensure_indexes(self):
        await self.db.games.create_index("chat_id", unique=True)
        await self.db.games.create_index([("status", 1), ("updated_at", -1)])
        await self.db.players.create_index("user_id", unique=True)

    async def get_game(self, chat_id):
        return await self.db.games.find_one({"chat_id": chat_id})

    async def save_game(self, game):
        game["updated_at"] = utcnow()
        await self.db.games.replace_one({"chat_id": game["chat_id"]}, game, upsert=True)

    async def delete_game(self, chat_id):
        await self.db.games.delete_one({"chat_id": chat_id})

    async def get_player(self, user_id):
        return await self.db.players.find_one({"user_id": user_id})

    async def upsert_player(self, user_id, username, first_name):
        await self.db.players.update_one(
            {"user_id": user_id},
            {"$set": {"username": username or "", "first_name": first_name or "", "updated_at": utcnow()},
             "$setOnInsert": {"user_id": user_id, "games": 0, "wins": 0, "losses": 0, "mvp": 0, "eliminations": 0}},
            upsert=True,
        )

    async def update_stats(self, user_id, games=0, wins=0, losses=0, mvp=0, eliminations=0):
        await self.db.players.update_one(
            {"user_id": user_id},
            {"$inc": {"games": games, "wins": wins, "losses": losses, "mvp": mvp, "eliminations": eliminations},
             "$set": {"updated_at": utcnow()}},
            upsert=True,
        )
