import datetime as dt
import asyncio
import logging
import uuid
import json
import aiormq
import aiormq.abc
from .utils import dict_from_json, dict_to_json


logger = logging.getLogger(__name__)


class AsyncRpcClient:
    EXCHANGE = ""
    EXCHANGE_TYPE = "direct"
    EXCHANGE_DURABLE = False
    QUEUE = ""
    ROUTING_KEY = ""
    EXCLUSIVE = True
    DURABLE = False
    RABBIT_URL = ""

    def __init__(self, amqp_url, exchange, queue, timeout=30):
        """Setup parameters to open a connection to RabbitMQ."""
        self.RABBIT_URL = amqp_url
        self.EXCHANGE = exchange
        self.QUEUE = queue
        self.timeout = timeout
        self.futures = {}
        self.loop = asyncio.get_running_loop()

    async def connect(self):
        """Establish channel, declare exchange and 'callback' queue for replies."""

        self.connection = await aiormq.connect(self.RABBIT_URL)

        self.channel = await self.connection.channel()
        await self.channel.exchange_declare(
            exchange=self.EXCHANGE,
            exchange_type=self.EXCHANGE_TYPE,
            durable=self.EXCHANGE_DURABLE,
        )
        declare_ok = await self.channel.queue_declare(
            queue=self.QUEUE, exclusive=self.EXCLUSIVE, durable=self.DURABLE
        )

        await self.channel.queue_bind(
            exchange=self.EXCHANGE,
            routing_key=self.ROUTING_KEY,
            queue=declare_ok.queue,
        )

        self.callback_queue = declare_ok.queue

        await self.channel.basic_consume(
            queue=self.callback_queue,
            consumer_callback=self.on_response,
        )

    async def disconnect(self):
        await self.connection.close()

    async def on_response(self, message: aiormq.abc.DeliveredMessage):
        json_body = json.loads(message.body, object_hook=dict_from_json)
        incoming_corr_id = (
            message.header.properties.correlation_id
            or json_body["meta"]["correlationId"]
        )
        if self.corr_id == incoming_corr_id:
            await self.channel.basic_ack(message.delivery_tag)
            future = self.futures.pop(message.header.properties.correlation_id)
            future.set_result(json_body)

    async def call(
        self,
        data,
        recipient,
        corr_id=None,
        routing_key="",
        exchange_type="direct",
        wait_response=True,
    ):
        await self.connect()
        self.corr_id = corr_id if corr_id else str(uuid.uuid4())
        future = self.loop.create_future()

        self.futures[self.corr_id] = future
        await self.channel.exchange_declare(
            exchange=recipient,
            exchange_type=exchange_type,
            durable=self.EXCHANGE_DURABLE,
        )
        message = {
            "meta": {
                "timestamp": dt.datetime.now().isoformat(),
                "source": self.EXCHANGE,
                "destination": recipient,
                "correlationId": self.corr_id,
            },
            "data": data,
        }

        await self.channel.basic_publish(
            exchange=recipient,
            routing_key=routing_key,
            body=json.dumps(message, default=dict_to_json).encode(),
            properties=aiormq.spec.Basic.Properties(
                reply_to=self.callback_queue if wait_response else None,
                correlation_id=self.corr_id,
            ),
        )
        result = True
        if wait_response:
            result = await asyncio.wait_for(future, timeout=self.timeout)
        await self.disconnect()
        return result
