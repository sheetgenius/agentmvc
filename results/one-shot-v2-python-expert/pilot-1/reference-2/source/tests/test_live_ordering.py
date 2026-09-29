import asyncio
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from conduit.live import Rooms, ShareConsumer


class ProbeConsumer(ShareConsumer):
    """Real consumer transitions with controllable transport backpressure."""

    def __init__(self, registry, *, delay_ready=False):
        super().__init__()
        self.scope = {"url_route": {"kwargs": {"share_id": "link"}}}
        self.registry = registry
        self.messages = []
        self.ready_started = asyncio.Event()
        self.release_ready = asyncio.Event()
        if not delay_ready:
            self.release_ready.set()
        self.delay_presence = False
        self.presence_started = asyncio.Event()
        self.release_presence = asyncio.Event()

    async def accept(self):
        pass

    async def close(self):
        pass

    async def send_json(self, content, **kwargs):
        assert not self.registry.lock.locked(), "Transport awaited under the room lock"
        if content["type"] == "ready":
            self.ready_started.set()
            await self.release_ready.wait()
        elif content["type"] == "presence" and self.delay_presence:
            self.delay_presence = False
            self.presence_started.set()
            await self.release_presence.wait()
        self.messages.append(content)


class LiveOrdering(SimpleTestCase):
    def run_room(self, scenario):
        async def exercise():
            registry = Rooms()
            article = SimpleNamespace(slug="slug", title="title", body="body", revision=1)
            link = SimpleNamespace(article=article, article_id=1)
            with (
                patch("conduit.live.rooms", registry),
                patch("conduit.live.share_for", return_value=link),
            ):
                await asyncio.wait_for(scenario(registry), timeout=5)

        asyncio.run(exercise())

    def test_simultaneous_joins_refresh_both_clients_after_delayed_ready(self):
        async def scenario(registry):
            first = ProbeConsumer(registry, delay_ready=True)
            second = ProbeConsumer(registry)
            await first.connect()
            await second.connect()
            a = asyncio.create_task(first.receive_json({"type": "subscribe", "key": "key"}))
            await first.ready_started.wait()
            b = asyncio.create_task(second.receive_json({"type": "subscribe", "key": "key"}))
            await second.ready_started.wait()
            first.release_ready.set()
            await asyncio.gather(a, b)
            for client in (first, second):
                self.assertEqual(client.messages[0]["type"], "ready")
                self.assertEqual(client.messages[-1], {"type": "presence", "count": 2})

        self.run_room(scenario)

    def test_overlapping_leaves_cannot_deliver_a_stale_final_count(self):
        async def scenario(registry):
            observer, second, third = [ProbeConsumer(registry) for _ in range(3)]
            for client in (observer, second, third):
                await client.connect()
                await client.receive_json({"type": "subscribe", "key": "key"})
            observer.delay_presence = True
            a = asyncio.create_task(second.disconnect(1000))
            await observer.presence_started.wait()
            b = asyncio.create_task(third.disconnect(1000))
            while third in registry.members["link"]:
                await asyncio.sleep(0)
            observer.release_presence.set()
            await asyncio.gather(a, b)
            self.assertEqual(observer.messages[-1], {"type": "presence", "count": 1})

        self.run_room(scenario)

    def test_ready_precedes_only_the_newest_pending_update(self):
        async def scenario(registry):
            client = ProbeConsumer(registry, delay_ready=True)
            await client.connect()
            task = asyncio.create_task(client.receive_json({"type": "subscribe", "key": "key"}))
            await client.ready_started.wait()
            article = {"slug": "slug", "title": "new", "body": "body", "revision": 3}
            await registry.updated(1, article)
            await registry.updated(1, {**article, "revision": 2})
            self.assertEqual(client.messages, [])
            client.release_ready.set()
            await task
            events = [m for m in client.messages if m["type"] in ("ready", "updated")]
            self.assertEqual([m["type"] for m in events], ["ready", "updated"])
            self.assertEqual([m["article"]["revision"] for m in events], [1, 3])

        self.run_room(scenario)

    def test_revocation_during_ready_prevents_a_later_pending_update(self):
        async def scenario(registry):
            client = ProbeConsumer(registry, delay_ready=True)
            await client.connect()
            ready = asyncio.create_task(client.receive_json({"type": "subscribe", "key": "key"}))
            await client.ready_started.wait()
            await registry.updated(
                1, {"slug": "slug", "title": "new", "body": "body", "revision": 2}
            )
            revoked = asyncio.create_task(registry.revoked("link"))
            while "link" in registry.members:
                await asyncio.sleep(0)
            client.release_ready.set()
            await asyncio.gather(ready, revoked)
            self.assertEqual([m["type"] for m in client.messages], ["ready", "revoked"])

        self.run_room(scenario)
