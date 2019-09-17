import os
import json
import datetime as dt
import pika
import uuid

class Publisher(object):
    """Client API Publisher"""

    EXCHANGE_TYPE = 'direct'
    PUBLISH_INTERVAL = 5
    EXCHANGE = "" 

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

    def publish_message(self, data, destination=None, corr_id=None):
        """
        Invoke this command to publish data to the destination

        Args:
            data: data to be sent
        """
        self.run()

        if not corr_id:
            corr_id = str(uuid.uuid4())

        message = {
            "meta": {
                "timestamp": dt.datetime.now().isoformat(),
                "source": self.EXCHANGE,
                "destination": destination,
                "correlationId": corr_id
            },
            "command": data,
        }

        properties = pika.BasicProperties(
            content_type='application/json',
            correlation_id=corr_id
        )

        self._channel.basic_publish(
            destination,
            '',
            json.dumps(message, ensure_ascii=False),
            properties
        )

        self.close_channel()
        self.close_connection()

    def run(self):
        """
        Invoke this command to connect, open channel and declare EXCHANGE.

        """
        self._connection = self.connect()  # open connection
        self._channel = self._connection.channel()  # open channel
        self._channel.exchange_declare(self.EXCHANGE, self.EXCHANGE_TYPE)  # declare queue
