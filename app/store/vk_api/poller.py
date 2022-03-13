import asyncio
from asyncio import Task, Future
from typing import Optional

from app.store import Store


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None
        self.queues: dict = {}

    async def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())

    async def stop(self):
        self.is_running = False
        await self.poll_task

    async def poll(self):
        while self.is_running:
            updates = await self.store.vk_api.poll()
            for update in updates:
                chat_id = str(update.object.peer_id)
                if self.queues.get(chat_id) is None:
                    self.queues[chat_id] = asyncio.Queue()
                self.queues[chat_id].put_nowait(update)

            tasks = []
            for queue in self.queues.values():
                task = asyncio.create_task(self.call_to_bot(queue))
                tasks.append(task)

                await queue.join()

            for task in tasks:
                task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)

    async def call_to_bot(self, queue: asyncio.Queue):
        while True:
            update = await queue.get()
            if not update:
                break

            await self.store.bots_manager.handle_update(update)
            queue.task_done()
