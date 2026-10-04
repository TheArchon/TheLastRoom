from html import escape
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def display_name(user):
    name = (user.first_name or "").strip()
    if user.last_name:
        name += " " + user.last_name
    return escape(name or user.username or str(user.id))


def game_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚪 Join Game", callback_data="game:join"),
         InlineKeyboardButton("🚪 Leave Game", callback_data="game:leave")],
        [InlineKeyboardButton("▶️ Start Game", callback_data="game:start")],
        [InlineKeyboardButton("❌ Cancel", callback_data="game:cancel")],
    ])


def action_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Investigate", callback_data="act:investigate"),
         InlineKeyboardButton("👁️ CCTV", callback_data="act:cctv")],
        [InlineKeyboardButton("🧩 Search", callback_data="act:search"),
         InlineKeyboardButton("🤝 Trust", callback_data="act:trust")],
        [InlineKeyboardButton("🛡️ Secure", callback_data="act:secure")],
    ])


def impostor_action_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚠️ Sabotage", callback_data="act:sabotage")],
        [InlineKeyboardButton("👁️ CCTV", callback_data="act:cctv"),
         InlineKeyboardButton("🧩 Search", callback_data="act:search")],
        [InlineKeyboardButton("🛡️ Secure", callback_data="act:secure")],
    ])


def vote_keyboard(player_ids, names):
    rows = []
    for uid in player_ids:
        rows.append([InlineKeyboardButton(f"🗳️ {names[uid]}", callback_data=f"vote:{uid}")])
    rows.append([InlineKeyboardButton("⏭️ Abstain", callback_data="vote:0")])
    return InlineKeyboardMarkup(rows)


def result_text(game):
    return game.get("result_text", "Game finished.")


def html_custom_emoji(emoji, emoji_id):
    return f"<tg-emoji emoji-id='{emoji_id}'>{emoji}</tg-emoji>"
