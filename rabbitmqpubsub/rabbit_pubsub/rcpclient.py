import pika
import datetime as dt
import json
# import os
import uuid


class RpcClient(object):
    """Remote Procedure Call"""

    EXCHANGE = ""
    EXCHANGE_TYPE = 'direct'
    QUEUE = ''
    ROUTING_KEY = ''
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
        self.channel.exchange_declare(exchange=self.EXCHANGE,
                                      exchange_type=self.EXCHANGE_TYPE)
        result = self.channel.queue_declare(queue=self.QUEUE, exclusive=self.EXCLUSIVE, durable=self.DURABLE)

        self.channel.queue_bind(exchange=self.EXCHANGE,
                                routing_key=self.ROUTING_KEY,
                                queue=result.method.queue)

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
        try:
            json_body = json.loads(body)
            if self.corr_id == props.correlation_id or self.corr_id == json_body['meta']['correlationId']:
                self.channel.basic_ack(method.delivery_tag)
                self.response = body
        except Exception as e:
            print(str(e))

    def call(self, data, recipient, corr_id=None, routing_key="", exchange_type='direct'):
        """" Main call method - it does the actual RPC request.

        In this method we open connection and activate consumer, than add timeout, next we take a unique parametar\
        correlation_id and save it - the 'on_response' callback function will use this value to catch the\
        appropriate responce. Next we publish the request message, with two properties: reply_to\
        and correlation_id. Than wait until the proper response arrives and finally we return \
        the response back to user.
        """
        try:
            self.connect()
            # self.connection.add_timeout(
            #     self.timeout,
            #     self.disconnect
            # )
            self.response = None
            self.corr_id = corr_id if corr_id else str(uuid.uuid4())
            self.channel.exchange_declare(exchange=recipient, exchange_type=exchange_type)
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
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    reply_to=self.callback_queue,
                    correlation_id=self.corr_id
                )
            )
            start_time = dt.datetime.now() + dt.timedelta(seconds=self.timeout)
            while self.response is None:
                if start_time <= dt.datetime.now():
                    break
                self.connection.process_data_events()
            self.disconnect()
        except Exception as e:
            print(str(e))
        return self.response
