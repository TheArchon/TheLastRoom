import asyncio
import random
from collections import Counter
from datetime import datetime, timezone

from pyrogram import Client
from pyrogram.types import Message

from config import Config
from constants import SCENARIO
from database import Database
from game.roles import assign_roles, role_message
from game.scenario import action_clue, round_story
from utils import game_keyboard, action_keyboard, impostor_action_keyboard, vote_keyboard, display_name


def now_ts():
    return datetime.now(timezone.utc).timestamp()


class GameEngine:
    def __init__(self, app: Client, db: Database):
        self.app = app
        self.db = db
        self.locks = {}

    def lock_for(self, chat_id):
        return self.locks.setdefault(chat_id, asyncio.Lock())

    async def new_game(self, message: Message):
        async with self.lock_for(message.chat.id):
            old = await self.db.get_game(message.chat.id)
            if old and old.get("status") not in ("finished", "cancelled"):
                await message.reply_text("⚠️ A game/lobby is already active in this group.")
                return
            host = message.from_user
            game = {
                "chat_id": message.chat.id,
                "status": "lobby",
                "host_id": host.id,
                "players": {str(host.id): {"id": host.id, "name": display_name(host)}},
                "roles": {},
                "alive": [],
                "round": 0,
                "actions": {},
                "votes": {},
                "eliminated": [],
                "history": [],
                "created_at": now_ts(),
                "updated_at": now_ts(),
            }
            await self.db.save_game(game)
            await message.reply_text(
                "🔐 <b>THE LAST ROOM</b>\n\n"
                "A mystery has begun.\n"
                f"👥 Players: 1/{Config.LOBBY_MAX}\n"
                f"🧩 Minimum required: {Config.LOBBY_MIN}\n\n"
                "Join the lobby, then the host can start the game.",
                reply_markup=game_keyboard(),
            )

    async def join(self, query):
        chat_id = query.message.chat.id
        async with self.lock_for(chat_id):
            game = await self.db.get_game(chat_id)
            if not game or game.get("status") != "lobby":
                await query.answer("No active lobby.", show_alert=True)
                return
            uid = query.from_user.id
            if str(uid) in game["players"]:
                await query.answer("You are already in.", show_alert=True)
                return
            if len(game["players"]) >= Config.LOBBY_MAX:
                await query.answer("Lobby is full.", show_alert=True)
                return
            game["players"][str(uid)] = {"id": uid, "name": display_name(query.from_user)}
            await self.db.upsert_player(uid, query.from_user.username, query.from_user.first_name)
            await self.db.save_game(game)
            await query.answer("Joined the game! Check your private chat when it starts.")
            await self._refresh_lobby(query.message, game)

    async def leave(self, query):
        chat_id = query.message.chat.id
        async with self.lock_for(chat_id):
            game = await self.db.get_game(chat_id)
            if not game or game.get("status") != "lobby":
                await query.answer("Lobby is not active.", show_alert=True)
                return
            uid = query.from_user.id
            if str(uid) not in game["players"]:
                await query.answer("You are not in the lobby.", show_alert=True)
                return
            if uid == game["host_id"]:
                await query.answer("Host cannot leave. Cancel the lobby instead.", show_alert=True)
                return
            game["players"].pop(str(uid), None)
            await self.db.save_game(game)
            await query.answer("You left the lobby.")
            await self._refresh_lobby(query.message, game)

    async def cancel(self, query):
        chat_id = query.message.chat.id
        async with self.lock_for(chat_id):
            game = await self.db.get_game(chat_id)
            if not game or game.get("status") != "lobby":
                await query.answer("No lobby to cancel.", show_alert=True)
                return
            if query.from_user.id != game["host_id"]:
                await query.answer("Only the host can cancel.", show_alert=True)
                return
            game["status"] = "cancelled"
            await self.db.save_game(game)
            await query.answer("Lobby cancelled.")
            await query.message.edit_text("❌ <b>Lobby cancelled.</b>")

    async def start(self, query):
        chat_id = query.message.chat.id
        async with self.lock_for(chat_id):
            game = await self.db.get_game(chat_id)
            if not game or game.get("status") != "lobby":
                await query.answer("No active lobby.", show_alert=True)
                return
            if query.from_user.id != game["host_id"]:
                await query.answer("Only the host can start the game.", show_alert=True)
                return
            if len(game["players"]) < Config.LOBBY_MIN:
                await query.answer(f"Need at least {Config.LOBBY_MIN} players.", show_alert=True)
                return
            game["roles"] = {str(k): v for k, v in assign_roles([p["id"] for p in game["players"].values()]).items()}
            game["alive"] = [p["id"] for p in game["players"].values()]
            game["status"] = "round_actions"
            game["round"] = 1
            game["actions"] = {}
            game["votes"] = {}
            game["names"] = {str(p["id"]): p["name"] for p in game["players"].values()}
            game["round_deadline"] = now_ts() + Config.ROUND_SECONDS
            await self.db.save_game(game)

            failed_private = []
            for uid, role in game["roles"].items():
                try:
                    await self.app.send_message(uid, role_message(role))
                except Exception:
                    failed_private.append(uid)

            if failed_private:
                # Do not let players with blocked private chat participate in a game
                for uid in failed_private:
                    game["alive"].remove(uid)
                    game["players"].pop(str(uid), None)
                    game["roles"].pop(str(uid), None)
                if len(game["alive"]) < Config.LOBBY_MIN:
                    game["status"] = "cancelled"
                    await self.db.save_game(game)
                    await query.message.edit_text(
                        "❌ Game cancelled because some players have not opened the bot in private chat.\n"
                        "Ask every player to open the bot and press /start, then create a new game."
                    )
                    return
                # Reassign from scratch to keep role counts valid.
                game["roles"] = {str(k): v for k, v in assign_roles(game["alive"]).items()}
                await self.db.save_game(game)
                for uid, role in game["roles"].items():
                    try:
                        await self.app.send_message(uid, role_message(role))
                    except Exception:
                        pass

            await query.answer("Game started!")
            await query.message.edit_text(
                f"🔐 <b>{SCENARIO['title']}</b>\n\n"
                f"{SCENARIO['intro']}\n\n"
                f"👥 Players: {len(game['alive'])}\n"
                "📩 Check your private chat for your role and instructions."
            )
            await self._start_round(chat_id, 1)

    async def _refresh_lobby(self, message, game):
        names = [p["name"] for p in game["players"].values()]
        text = (
            "🔐 <b>THE LAST ROOM</b>\n\n"
            f"👥 <b>Players ({len(names)}/{Config.LOBBY_MAX})</b>\n" +
            "\n".join(f"• {n}" for n in names) +
            f"\n\nMinimum: {Config.LOBBY_MIN}\nHost: {game['players'].get(str(game['host_id']), {}).get('name', 'Host')}"
        )
        await message.edit_text(text, reply_markup=game_keyboard())

    async def _start_round(self, chat_id, round_no):
        game = await self.db.get_game(chat_id)
        if not game or game.get("status") in ("finished", "cancelled"):
            return
        game["status"] = "round_actions"
        game["round"] = round_no
        game["actions"] = {}
        game["round_deadline"] = now_ts() + Config.ROUND_SECONDS
        await self.db.save_game(game)
        story = round_story(round_no)
        await self.app.send_message(
            chat_id,
            f"🔔 <b>{story['title']}</b>\n\n{story['story']}\n\n"
            f"⏳ You have about {Config.ROUND_SECONDS} seconds to choose your private action."
        )
        for uid in game["alive"]:
            try:
                role = game["roles"].get(str(uid))
                markup = impostor_action_keyboard() if role == "impostor" else action_keyboard()
                await self.app.send_message(uid, f"🎮 <b>Round {round_no}</b>\nChoose one action:", reply_markup=markup)
            except Exception:
                pass

    async def action(self, query, action):
        uid = query.from_user.id
        games = self.db.db.games.find({"status": "round_actions", "alive": uid})
        found = await games.to_list(length=1)
        game = found[0] if found else None
        if not game:
            await query.answer("No active game found.", show_alert=True)
            return
        chat_id = game["chat_id"]
        if not game or game.get("status") != "round_actions" or uid not in game.get("alive", []):
            await query.answer("This action is no longer available.", show_alert=True)
            return
        async with self.lock_for(chat_id):
            game = await self.db.get_game(chat_id)
            if uid in game["actions"]:
                await query.answer("You already chose an action this round.", show_alert=True)
                return
            role = game["roles"].get(str(uid))
            if action == "sabotage" and role != "impostor":
                await query.answer("Only the Impostor can sabotage.", show_alert=True)
                return
            game["actions"][str(uid)] = action
            clue = action_clue(role, action, game["round"], game)
            game.setdefault("history", []).append({"round": game["round"], "uid": uid, "action": action})
            await self.db.save_game(game)
            await query.answer("Choice recorded.")
            try:
                await query.message.edit_text("✅ <b>Choice locked.</b>\n\nYour clue:\n" + clue)
            except Exception:
                pass
            if len(game["actions"]) >= len(game["alive"]):
                await self._start_voting(chat_id)

    async def _start_voting(self, chat_id):
        async with self.lock_for(chat_id):
            game = await self.db.get_game(chat_id)
            if not game or game.get("status") != "round_actions":
                return
            game["status"] = "voting"
            game["votes"] = {}
            game["vote_deadline"] = now_ts() + Config.VOTE_SECONDS
            await self.db.save_game(game)
            ids = [uid for uid in game["alive"]]
            names = {uid: game["names"].get(str(uid), str(uid)) for uid in ids}
            await self.app.send_message(
                chat_id,
                f"🗳️ <b>Voting — Round {game['round']}</b>\n\n"
                "Discuss in the group and vote for the player you suspect."
            )
            for uid in ids:
                try:
                    await self.app.send_message(uid, "🗳️ <b>Cast your vote privately:</b>",
                                                reply_markup=vote_keyboard(ids, names))
                except Exception:
                    pass

    async def vote(self, query, target_id):
        uid = query.from_user.id
        games = self.db.db.games.find({"status": "voting", "alive": uid})
        found = await games.to_list(length=1)
        game = found[0] if found else None
        if not game:
            await query.answer("No active vote.", show_alert=True)
            return
        chat_id = game["chat_id"]
        async with self.lock_for(chat_id):
            game = await self.db.get_game(chat_id)
            if uid in game.get("votes", {}):
                await query.answer("Your vote is already locked.", show_alert=True)
                return
            if target_id != 0 and target_id not in game["alive"]:
                await query.answer("Invalid target.", show_alert=True)
                return
            game["votes"][str(uid)] = int(target_id)
            await self.db.save_game(game)
            await query.answer("Vote recorded.")
            try:
                await query.message.edit_text("✅ <b>Vote locked.</b>")
            except Exception:
                pass
            if len(game["votes"]) >= len(game["alive"]):
                await self._resolve_vote(chat_id)

    async def _resolve_vote(self, chat_id):
        async with self.lock_for(chat_id):
            game = await self.db.get_game(chat_id)
            if not game or game.get("status") != "voting":
                return
            counts = Counter(v for v in game["votes"].values() if int(v) != 0)
            eliminated = None
            if counts:
                top = counts.most_common()
                if len(top) == 1 or top[0][1] > top[1][1]:
                    eliminated = int(top[0][0])
            if eliminated and eliminated in game["alive"]:
                game["alive"].remove(eliminated)
                game["eliminated"].append(eliminated)
                await self.db.update_stats(eliminated, eliminations=1)
                name = game["names"].get(str(eliminated), str(eliminated))
                await self.app.send_message(chat_id, f"🚨 <b>{name}</b> has been eliminated by the vote.")
            else:
                await self.app.send_message(chat_id, "⚖️ The vote was tied or everyone abstained. Nobody is eliminated.")

            game["history"].append({"round": game["round"], "vote_counts": dict(counts), "eliminated": eliminated})
            if await self._should_end(game):
                await self._finish(game)
                return

            if game["round"] >= len(SCENARIO["rounds"]):
                await self._finish(game)
                return

            game["status"] = "transition"
            await self.db.save_game(game)
            next_round = game["round"] + 1
        await self._start_round(chat_id, next_round)

    async def _should_end(self, game):
        alive = game["alive"]
        impostor_alive = any(game["roles"].get(str(uid)) == "impostor" for uid in alive)
        non_impostors = sum(game["roles"].get(str(uid)) != "impostor" for uid in alive)
        return not impostor_alive or non_impostors <= 1 or not alive

    async def _finish(self, game):
        impostor = next((uid for uid, role in game["roles"].items() if role == "impostor"), None)
        impostor_alive = impostor in game["alive"] if impostor else False
        if not impostor_alive:
            outcome = "🕵️ <b>THE GROUP WINS</b>\nThe Impostor was exposed."
            winners = [int(uid) for uid in game["players"] if game["roles"].get(str(uid)) != "impostor"]
        else:
            outcome = "🎭 <b>THE IMPOSTOR WINS</b>\nThe group failed to stop the sabotage."
            winners = [impostor] if impostor else []

        # Special ending based on the final round's actions.
        final_sabotage = any(
            h.get("round") == len(SCENARIO["rounds"]) and h.get("action") == "sabotage"
            for h in game.get("history", [])
        )
        if impostor_alive and final_sabotage:
            outcome += "\n\n💀 <b>Ending: BLACKOUT</b>\nThe facility goes completely dark."
        elif not impostor_alive and game.get("round", 0) >= 3:
            outcome += "\n\n🚪 <b>Ending: ESCAPE</b>\nThe final room unlocks and the survivors escape."
        else:
            outcome += "\n\n❓ <b>Ending: UNCERTAIN</b>\nSome questions remain unanswered."

        mvp = None
        if game.get("history"):
            scores = Counter()
            for h in game["history"]:
                if "uid" in h:
                    scores[h["uid"]] += 1
            if scores:
                mvp = scores.most_common(1)[0][0]

        game["status"] = "finished"
        game["result_text"] = outcome
        game["finished_at"] = now_ts()
        await self.db.save_game(game)

        for uid in game["players"]:
            uid_int = int(uid)
            won = uid_int in winners
            await self.db.update_stats(uid_int, games=1, wins=int(won), losses=int(not won), mvp=int(uid_int == mvp))
        for uid, role in game["roles"].items():
            try:
                await self.app.send_message(int(uid), f"🏁 <b>GAME OVER</b>\n\nYour role was: {role.title()}\n\n{outcome}")
            except Exception:
                pass

        names = game["names"]
        role_lines = "\n".join(
            f"• {names.get(str(uid), uid)} — {role}"
            for uid, role in game["roles"].items()
        )
        await self.app.send_message(
            game["chat_id"],
            f"🏁 <b>THE LAST ROOM — GAME OVER</b>\n\n{outcome}\n\n"
            f"🎭 <b>Role Reveal</b>\n{role_lines}\n\n"
            "Use /newgame to play again."
        )

    async def tick(self):
        cursor = self.db.db.games.find({"status": {"$in": ["round_actions", "voting"]}})
        games = await cursor.to_list(length=100)
        for game in games:
            deadline = game.get("round_deadline") if game["status"] == "round_actions" else game.get("vote_deadline")
            if deadline and now_ts() >= deadline:
                if game["status"] == "round_actions":
                    await self._start_voting(game["chat_id"])
                else:
                    await self._resolve_vote(game["chat_id"])
