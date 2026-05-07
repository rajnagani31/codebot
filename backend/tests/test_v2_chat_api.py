import asyncio
import json
import unittest
from unittest.mock import patch

from backend.bot.application.router.v2 import chat_api


class FakePubSub:
    def __init__(self, messages):
        self.messages = list(messages)
        self.subscribed = []
        self.unsubscribed = []
        self.closed = False

    def subscribe(self, channel):
        self.subscribed.append(channel)

    def unsubscribe(self, channel):
        self.unsubscribed.append(channel)

    def close(self):
        self.closed = True

    def get_message(self, ignore_subscribe_messages=True, timeout=1.0):
        if self.messages:
            return self.messages.pop(0)
        return None


class FakeRedis:
    def __init__(self, pubsub):
        self._pubsub = pubsub

    def pubsub(self):
        return self._pubsub


class ChatApiV2Tests(unittest.TestCase):
    def test_event_generator_yields_matching_trade_payload(self):
        payload = {"user_id": "7", "item_id": "abc-123", "status": "BUY"}
        fake_pubsub = FakePubSub(
            [
                {"type": "message", "data": "not-json"},
                {"type": "message", "data": json.dumps(payload)},
            ]
        )

        async def run_test():
            with patch.object(chat_api, "rq", FakeRedis(fake_pubsub)):
                generator = chat_api.event_generator(7)
                first = await anext(generator)
                second = await anext(generator)
                await generator.aclose()
                return first, second

        first, second = asyncio.run(run_test())

        self.assertIn("event: connected", first)
        self.assertIn('"user_id": 7', first)
        self.assertIn('"item_id": "abc-123"', second)
        self.assertIn('"status": "BUY"', second)
        self.assertEqual(fake_pubsub.subscribed, ["trade_channel"])
        self.assertEqual(fake_pubsub.unsubscribed, ["trade_channel"])
        self.assertTrue(fake_pubsub.closed)

    def test_notification_stream_sends_initial_event_without_waiting_for_redis(self):
        fake_pubsub = FakePubSub([])

        async def run_test():
            with patch.object(chat_api, "rq", FakeRedis(fake_pubsub)):
                response = await chat_api.notification_stream(42)
                first_chunk = await anext(response.body_iterator)
                await response.body_iterator.aclose()
                return first_chunk

        first_chunk = asyncio.run(run_test())

        self.assertIn("event: connected", first_chunk)
        self.assertIn('"user_id": 42', first_chunk)
        self.assertEqual(fake_pubsub.subscribed, ["trade_channel"])
        self.assertEqual(fake_pubsub.unsubscribed, ["trade_channel"])
        self.assertTrue(fake_pubsub.closed)
