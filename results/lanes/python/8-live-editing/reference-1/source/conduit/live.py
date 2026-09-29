"""Single-process editing rooms. Database snapshots remain the source of truth."""

import asyncio
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .sharing import room_name, shared_article, valid_link

ROOM_LIMIT = 100
rooms = {}


@database_sync_to_async
def authorized_snapshot(share_id, key):
    link = valid_link(share_id, key)
    return shared_article(link.article) if link else None


class EditingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.share_id = self.scope["url_route"]["kwargs"]["share_id"]
        self.group = room_name(self.share_id)
        self.subscribed = False
        self.admitted = False
        self.revision = 0
        await self.accept()
        self.deadline = asyncio.create_task(self.expire_subscription())

    async def expire_subscription(self):
        await asyncio.sleep(4)
        if not self.subscribed:
            await self.reject("invalid_link")

    async def receive(self, text_data=None, bytes_data=None):
        if self.subscribed:
            return
        self.subscribed = True
        self.deadline.cancel()
        try:
            message = json.loads(text_data) if text_data is not None else None
        except ValueError:
            message = None
        if not isinstance(message, dict) or message.get("type") != "subscribe":
            await self.reject("invalid_link")
            return

        # Register before reading the snapshot: a concurrent commit then reaches
        # either this read or the group's queued update.
        await self.channel_layer.group_add(self.group, self.channel_name)
        snapshot = await authorized_snapshot(self.share_id, message.get("key"))
        if snapshot is None:
            await self.reject("invalid_link")
            return
        members = rooms.setdefault(self.group, set())
        if len(members) >= ROOM_LIMIT:
            await self.reject("room_full", limit=ROOM_LIMIT)
            return
        members.add(self.channel_name)
        self.admitted = True
        self.revision = snapshot["revision"]
        count = len(members)
        await self.send_json({"type": "ready", "article": snapshot, "presence": count})
        await self.channel_layer.group_send(
            self.group, {"type": "presence_changed", "joined": self.channel_name}
        )

    async def reject(self, kind, **extra):
        await self.send_json({"type": kind, **extra})
        await self.close()

    async def send_json(self, message):
        await self.send(text_data=json.dumps(message))

    async def article_updated(self, event):
        if self.admitted and event["article"]["revision"] > self.revision:
            self.revision = event["article"]["revision"]
            await self.send_json({"type": "updated", "article": event["article"]})

    async def presence_changed(self, event):
        if self.admitted and event.get("joined") != self.channel_name:
            await self.send_json({"type": "presence", "count": len(rooms.get(self.group, ()))})

    async def link_revoked(self, event):
        if self.admitted:
            await self.reject("revoked")

    async def disconnect(self, close_code):
        self.deadline.cancel()
        if self.admitted:
            members = rooms[self.group]
            members.discard(self.channel_name)
            if members:
                await self.channel_layer.group_send(self.group, {"type": "presence_changed"})
            else:
                rooms.pop(self.group, None)
        if self.subscribed:
            await self.channel_layer.group_discard(self.group, self.channel_name)
