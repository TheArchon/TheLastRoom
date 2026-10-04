from pyrogram import filters
from pyrogram.types import Message
from utils import display_name


def register_command_handlers(app, engine):
    @app.on_message(filters.command("start") & filters.private)
    async def start_private(_, message: Message):
        await engine.db.upsert_player(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await message.reply_text(
            "🔐 <b>THE LAST ROOM</b>\n\n"
            "Welcome. This is your private control room.\n\n"
            "Add me to a group, then use /newgame there.\n"
            "Keep this chat open so I can send you secret roles, clues and votes."
        )

    @app.on_message(filters.command("help"))
    async def help_handler(_, message: Message):
        await message.reply_text(
            "<b>THE LAST ROOM — V1</b>\n\n"
            "/newgame — Create a group lobby\n"
            "/profile — View your stats\n"
            "/help — Show help\n\n"
            "Game flow: Lobby → secret roles → actions → discussion → vote → ending."
        )

    @app.on_message(filters.command("newgame") & filters.group)
    async def new_game_handler(_, message: Message):
        await engine.new_game(message)

    @app.on_message(filters.command("profile"))
    async def profile_handler(_, message: Message):
        p = await engine.db.get_player(message.from_user.id)
        if not p:
            await engine.db.upsert_player(message.from_user.id, message.from_user.username, message.from_user.first_name)
            p = await engine.db.get_player(message.from_user.id)
        await message.reply_text(
            f"👤 <b>{display_name(message.from_user)}</b>\n\n"
            f"🎮 Games: {p.get('games', 0)}\n"
            f"🏆 Wins: {p.get('wins', 0)}\n"
            f"💀 Losses: {p.get('losses', 0)}\n"
            f"⭐ MVP: {p.get('mvp', 0)}\n"
            f"🚨 Eliminations: {p.get('eliminations', 0)}"
        )
