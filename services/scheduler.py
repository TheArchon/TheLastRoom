import asyncio
import logging

log = logging.getLogger("last_room.scheduler")


class GameScheduler:
    def __init__(self, engine, interval=2):
        self.engine = engine
        self.interval = interval
        self.task = None
        self.running = False

    async def start(self):
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._loop())

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def _loop(self):
        while self.running:
            try:
                await self.engine.tick()
            except Exception:
                log.exception("Scheduler tick failed")
            await asyncio.sleep(self.interval)
