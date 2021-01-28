from asyncio import Queue
import asyncio

from loguru import logger

class AsyncQueue:
    def __init__(self, auto_start=True) -> None:
        self.queue = Queue()
        self.loop_on: asyncio.Task = None
        if auto_start:
            self.start()

    def start(self):
        if self.loop_on is None or self.loop_on.done():
            extra = "init"
            if self.loop_on is not None and self.loop_on.exception() is not None:
                logger.error(self.loop_on.exception())
                self.loop_on.print_stack()
            logger.debug(f"loop starting. ")
            self.loop_on = asyncio.Task(self.loop())

    async def loop(self):
        while True:
            task, event, result = await self.queue.get()
            try:
                logger.debug(f"got task")
                done, _ = await asyncio.wait([task])
                first = list(done)[0]
                result.append(first.result())
                logger.debug(f"pickup {result}")
            finally:
                event.set()
                logger.debug(f"event complete")

    async def run(self, task):
        self.start()
        logger.debug(f"prepare task")
        event = asyncio.Event()
        result = []
        await self.queue.put([task, event, result])
        logger.debug(f"task enqueued")
        await event.wait()
        logger.debug(f"task completed")
        return result[0]
        
