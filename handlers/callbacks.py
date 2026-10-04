from pyrogram import filters


def register_callback_handlers(app, engine):
    @app.on_callback_query(filters.regex(r"^game:"))
    async def game_callback(_, query):
        action = query.data.split(":", 1)[1]
        if action == "join":
            await engine.join(query)
        elif action == "leave":
            await engine.leave(query)
        elif action == "start":
            await engine.start(query)
        elif action == "cancel":
            await engine.cancel(query)

    @app.on_callback_query(filters.regex(r"^act:"))
    async def action_callback(_, query):
        await engine.action(query, query.data.split(":", 1)[1])

    @app.on_callback_query(filters.regex(r"^vote:"))
    async def vote_callback(_, query):
        await engine.vote(query, int(query.data.split(":", 1)[1]))
