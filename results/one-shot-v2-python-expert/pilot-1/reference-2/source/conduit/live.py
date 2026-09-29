import asyncio

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .domain import RuleError, share_for, shared_json


class Rooms:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.members = {}
        self.loop = None

    async def join(self, client, share_id, key):
        async with self.lock:
            try:
                article_id, article = await database_sync_to_async(
                    lambda: (lambda link: (link.article_id, shared_json(link.article)))(
                        share_for(share_id, key)
                    )
                )()
            except RuleError:
                return "invalid_link", None, 0, None
            room = self.members.setdefault(share_id, set())
            if len(room) >= 100:
                return "room_full", None, 0, None
            room.add(client)
            count = len(room)
        return "ready", article, count, article_id

    async def leave(self, client):
        if not client.admitted:
            return
        async with self.lock:
            room = self.members.get(client.share_id)
            if room is None or client not in room:
                return
            room.remove(client)
            if not room:
                del self.members[client.share_id]
        await self.presence(client.share_id)

    async def presence(self, share_id):
        async with self.lock:
            targets = tuple(self.members.get(share_id, ()))
        await asyncio.gather(*(client.presence() for client in targets), return_exceptions=True)

    async def updated(self, article_id, article):
        async with self.lock:
            targets = tuple(
                client
                for room in self.members.values()
                for client in room
                if client.article_id == article_id
            )
        await asyncio.gather(
            *(client.update(article) for client in targets), return_exceptions=True
        )

    async def revoked(self, share_id):
        async with self.lock:
            targets = tuple(self.members.pop(share_id, ()))
        await asyncio.gather(*(client.revoke() for client in targets), return_exceptions=True)


rooms = Rooms()


def dispatch(coro):
    if rooms.loop and rooms.loop.is_running():
        rooms.loop.call_soon_threadsafe(lambda: asyncio.create_task(coro()))


def broadcast_after_commit(article_id, article):
    dispatch(lambda: rooms.updated(article_id, article))


def revoke_after_commit(share_id):
    dispatch(lambda: rooms.revoked(share_id))


class ShareConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        rooms.loop = asyncio.get_running_loop()
        self.share_id = self.scope["url_route"]["kwargs"]["share_id"]
        self.admitted = False
        self.ready = False
        self.revision = 0
        self.pending = None
        self.send_lock = asyncio.Lock()
        await self.accept()
        self.timeout = asyncio.create_task(self.expire())

    async def expire(self):
        await asyncio.sleep(5)
        if not self.admitted:
            await self.close()

    async def receive_json(self, content, **kwargs):
        if self.admitted:
            return
        if not isinstance(content, dict) or content.get("type") != "subscribe":
            await self.send_json({"type": "invalid_link"})
            await self.close()
            return
        result, article, count, article_id = await rooms.join(
            self, self.share_id, content.get("key")
        )
        if result != "ready":
            await self.send_json(
                {"type": result, **({"limit": 100} if result == "room_full" else {})}
            )
            await self.close()
            return
        self.admitted = True
        self.timeout.cancel()
        self.article_id = article_id
        self.revision = article["revision"]
        async with self.send_lock:
            await self.send_json({"type": "ready", "article": article, "presence": count})
            self.ready = True
        if self.pending and self.pending["revision"] > self.revision:
            await self.update(self.pending)
        await rooms.presence(self.share_id)

    async def presence(self):
        async with self.send_lock:
            if not self.ready or not self.admitted:
                return
            async with rooms.lock:
                members = rooms.members.get(self.share_id, ())
                if self not in members:
                    return
                count = len(members)
            await self.send_json({"type": "presence", "count": count})

    async def update(self, article):
        if not self.ready:
            if not self.pending or article["revision"] > self.pending["revision"]:
                self.pending = article
            return
        async with self.send_lock:
            if not self.admitted or article["revision"] <= self.revision:
                return
            self.revision = article["revision"]
            await self.send_json({"type": "updated", "article": article})

    async def revoke(self):
        async with self.send_lock:
            self.admitted = False
            await self.send_json({"type": "revoked"})
            await self.close()

    async def disconnect(self, code):
        self.timeout.cancel()
        await rooms.leave(self)
