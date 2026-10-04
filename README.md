# THE LAST ROOM — V1

A Telegram multiplayer mystery/social-deduction game built with Kurigram (Pyrogram-compatible API) and MongoDB/Motor.

## V1 features

- 4–10 player group games
- Lobby with join/leave/start/cancel
- Private role assignment
- 5 roles: Impostor, Detective, Analyst, Witness, Survivor
- Private clues and actions
- 3 story rounds
- Group discussion
- Private voting
- Vote elimination / tie handling
- Multiple endings
- Role reveal
- Player stats and MVP
- Persistent game state in MongoDB
- Background round/vote timers
- Basic recovery-friendly architecture
- Customizable scenario data

## Requirements

- Python 3.10+
- Telegram bot token
- Telegram API ID/API hash
- MongoDB (local or MongoDB Atlas)

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python bot.py
```

Every player must open the bot in private chat and press `/start` before joining a game. This is required because Telegram bots cannot start arbitrary private conversations.

## Environment

See `.env.example`.

## VPS

For a small initial deployment, 2 vCPU / 2 GB RAM / 30–40 GB SSD is a sensible starting point. Monitor MongoDB and concurrent games before scaling.

## Commands

Private:
- `/start`
- `/profile`
- `/help`

Group:
- `/newgame`
- `/help`
- `/profile`

## Game flow

1. Host uses `/newgame` in a group.
2. Players join.
3. Host starts when at least 4 players are present.
4. Roles are sent privately.
5. Each round players choose one private action.
6. Clues are delivered privately.
7. Players discuss in the group.
8. Votes are collected privately.
9. Elimination and win conditions are resolved.
10. After up to 3 rounds, the ending and roles are revealed.

## Notes

Kurigram installs as the `kurigram` package while its compatible API is imported from `pyrogram`, matching the style of the supplied reference project.
