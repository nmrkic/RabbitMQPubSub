import pika
import datetime as dt
import json
import uuid
from .utils import dt_from_json, dt_to_json
import logging

logger = logging.getLogger(__name__)


class RpcClient(object):
    """Remote Procedure Call"""

    EXCHANGE = ""
    EXCHANGE_TYPE = "direct"
    EXCHANGE_DURABLE = False
    QUEUE = ""
    ROUTING_KEY = ""
    EXCLUSIVE = True
    DURABLE = False

    RABBIT_URL = ""
    QUEUE_TIMEOUT = 30

    def __init__(self, amqp_url, exchange, queue):
        """Setup parameters to open a connection to RabbitMQ."""
        self.RABBIT_URL = amqp_url
        self.EXCHANGE = exchange
        self.QUEUE = queue
        parameters = pika.URLParameters(self.RABBIT_URL)
        self.connection = pika.BlockingConnection(parameters)
        self.timeout = self.QUEUE_TIMEOUT
        self.response = None

    def connect(self):
        """Establish channel, declare exchange and 'callback' queue for replies."""

        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange=self.EXCHANGE,
            exchange_type=self.EXCHANGE_TYPE,
            durable=self.EXCHANGE_DURABLE,
        )
        result = self.channel.queue_declare(
            queue=self.QUEUE, exclusive=self.EXCLUSIVE, durable=self.DURABLE
        )

        self.channel.queue_bind(
            exchange=self.EXCHANGE,
            routing_key=self.ROUTING_KEY,
            queue=result.method.queue,
        )

        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
        )

    def disconnect(self):
        """Close connection after message is received or timeout expired."""
        self.connection.close()

    def on_response(self, ch, method, props, body):
        """Checks for every response message.

        Checks if the correlation_id is one we're looking for. If so, it\
        saves the response in self.response and breaks the consuming loop.

        """
        json_body = json.loads(body, object_hook=dt_from_json)
        if (
            self.corr_id == props.correlation_id
            or self.corr_id == json_body["meta"]["correlationId"]
        ):
            self.channel.basic_ack(method.delivery_tag)
            self.response = json_body

    def call(
        self, data, recipient, corr_id=None, routing_key="", exchange_type="direct"
    ):
        """ " Main call method - it does the actual RPC request.

        In this method we open connection and activate consumer,
        than add timeout, next we take a unique parameter
        correlation_id and save it - the 'on_response' callback
        function will use this value to catch the
        appropriate responce. Next we publish the request message,
        with two properties: reply_to
        and correlation_id. Than wait until the proper response
        arrives and finally we return
        the response back to user.
        """
        self.response = None
        self.connect()
        self.corr_id = corr_id if corr_id else str(uuid.uuid4())
        self.channel.exchange_declare(
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
        self.channel.basic_publish(
            exchange=recipient,
            routing_key=routing_key,
            body=json.dumps(message, default=dt_to_json),
            properties=pika.BasicProperties(
                reply_to=self.callback_queue, correlation_id=self.corr_id
            ),
        )
        start_time = dt.datetime.now() + dt.timedelta(seconds=self.timeout)
        while self.response is None:
            if start_time <= dt.datetime.now():
                raise Exception("Timeout occured waiting for response.")
            self.connection.process_data_events()
        self.disconnect()
        return self.response
