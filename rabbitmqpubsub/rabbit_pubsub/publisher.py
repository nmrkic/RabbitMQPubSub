# import os
import json
import datetime as dt
import pika
import uuid
from .utils import dict_to_json


class Publisher(object):
    """Client API Publisher"""

    EXCHANGE_TYPE = "direct"
    EXCHANGE_DURABLE = False
    PUBLISH_INTERVAL = 5
    EXCHANGE = "publish"

    def __init__(self, amqp_url):
        self._connection = None
        self._channel = None
        self._url = pika.URLParameters(amqp_url)
        self._closing = False

    def connect(self):
        """
        Opens connection to RabbitMQ

        """
        return pika.BlockingConnection(self._url)

    def close_connection(self):
        """
        Invoke this command to close the connection to RabbitMQ

        """
        self._closing = True
        self._connection.close()

    def close_channel(self):
        """
        Invoke this command to close the channel with RabbitMQ

        """
        if self._channel:
            self._channel.close()

    def publish_message(self, data, destination, source, corr_id=None):
        """
        Invoke this command to publish data to the destination

        Args:
            data: data to be sent
        """
        self.EXCHANGE = source
        self.run(destination)

        if not corr_id:
            corr_id = str(uuid.uuid4())

        message = {
            "meta": {
                "timestamp": dt.datetime.now().isoformat(),
                "source": self.EXCHANGE,
                "destination": destination,
                "correlationId": corr_id,
            },
            "data": data,
        }

        properties = pika.BasicProperties(
            content_type="application/json", correlation_id=corr_id
        )

        self._channel.basic_publish(
            destination, "", json.dumps(message, default=dict_to_json), properties
        )

        self.close_channel()
        self.close_connection()

    def run(self, destination):
        """
        Invoke this command to connect, open channel and declare EXCHANGE.

        """
        self._connection = self.connect()  # open connection
        self._channel = self._connection.channel()  # open channel
        self._channel.exchange_declare(
            exchange=destination,
            exchange_type=self.EXCHANGE_TYPE,
            durable=self.EXCHANGE_DURABLE,
        )  # declare queue
