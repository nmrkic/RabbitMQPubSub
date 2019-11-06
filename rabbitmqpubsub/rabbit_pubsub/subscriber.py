from threading import Thread
import functools
import logging
import time
import pika
import asyncio

from pika.adapters.asyncio_connection import AsyncioConnection


class Subscriber(Thread):
    
    EXCHANGE = ''
    EXCHANGE_TYPE = ''
    QUEUE = ''
    ROUTING_KEY = ''
    no_ack = False 
    DURABLE = True
    EXCLUSIVE = False

    def __init__(self, amqp_url, exchange=None, exchange_type=None, queue=None):
        """
        Create a new instance of the consumer class, passing in the AMQP
        URL used to connect to RabbitMQ.
        """
        Thread.__init__(self)
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._url = amqp_url
        self._observers = []
        self.EXCHANGE = str(exchange) if exchange else self.EXCHANGE
        self.EXCHANGE_TYPE = str(exchange_type) if exchange_type else self.EXCHANGE_TYPE
        self.QUEUE = str(queue) if queue else self.QUEUE
    

    def subscribe(self, observer):
        """
        This method subscribes observer to follow on_message events
        """
        handle_func = getattr(observer, 'handle', None)
        if not handle_func or not callable(handle_func):
            raise Exception("Class has to implement handle(self, body) function")
        
        self._observers.append(observer)

    def connect(self):
        """
        This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika.
        ------------------
        :rtype: pika.SelectConnection

        """
        asyncio.set_event_loop(asyncio.new_event_loop())
        return AsyncioConnection(
            parameters=pika.URLParameters(self._url),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_open_error_callback,

        )

    def on_connection_open(self, unused_connection):
        """
        This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.
        """
        # add on conection close callback
        self._connection.add_on_close_callback(self.on_connection_closed)
        self.open_channel()

    def on_open_error_callback(self, _unused_connection, err):
        print(_unused_connection, err)

    def on_connection_closed(self, connection, reply_code, reply_text):
        """
        This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.
        """

        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            
            self._connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        """
        Will be invoked by the IOLoop timer if the connection is
        closed. See the on_connection_closed method.
        """

        # This is the old connection IOLoop instance, stop its ioloop
        self._connection.ioloop.stop()

        if not self._closing:

            # Create a new connection
            self._connection = self.connect()

            # There is now a new connection, needs a new ioloop to run
            self._connection.ioloop.run_forever()

    def open_channel(self):
        """
        Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.

        """
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        """
        This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.
        ------------------
        parameters:
            - name: channel
            - description: The channel object
            - type: pika.channel.Channel
        """
        self._channel = channel
        # add on channel close callback
        self._channel.add_on_close_callback(self.on_channel_closed)
        self.setup_exchange(self.EXCHANGE)

    def on_channel_closed(self, channel, reply_code):
        """
        Invoked by pika when RabbitMQ unexpectedly closes the channel.

        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.
        """
        print(reply_code)
        self._connection.close()

    def setup_exchange(self, exchange_name):
        """
        Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC
        command. When it is complete, the on_exchange_declareok method will
        be invoked by pika.
        """

        self._channel.exchange_declare(
            exchange=exchange_name,
            callback=self.on_exchange_declareok,
            exchange_type=self.EXCHANGE_TYPE
        )

    def on_exchange_declareok(self, unused_frame):
        """
        Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.
        """

        self.setup_queue(self.QUEUE)

    def setup_queue(self, queue_name):
        """
        Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
        command. When it is complete, the on_queue_declareok method will
        be invoked by pika.
        """

        self._channel.queue_declare(
            queue=queue_name,
            callback=self.on_queue_declareok,
            durable=self.DURABLE,
            exclusive=self.EXCLUSIVE
        )

    def on_queue_declareok(self, method_frame):
        """
        Method invoked by pika when the Queue.Declare RPC call made in
        setup_queue has completed. In this method we will bind the queue
        and exchange together with the routing key by issuing the Queue.Bind
        RPC command. When this command is complete, the on_bindok method will
        be invoked by pika.
        """

        self._channel.queue_bind(
            queue=self.QUEUE,
            exchange=self.EXCHANGE,
            routing_key=self.ROUTING_KEY,
            callback=self.on_bindok,
        )

    def on_bindok(self, unused_frame):
        """
        Invoked by pika when the Queue.Bind method has completed. At this
        point we will start consuming messages by calling start_consuming
        which will invoke the needed RPC commands to start the process.
        """
        self.start_consuming()

    def start_consuming(self):
        """
        This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.

        """
        # add on cancel callback
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

        self._consumer_tag = self._channel.basic_consume(
            queue=self.QUEUE,
            auto_ack=self.no_ack,
            on_message_callback=self.on_message,
        )

    def on_consumer_cancelled(self, method_frame):
        """
        Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.
        """

        if self._channel:
            self._channel.close()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        """
        Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.
        """

        for observer in self._observers:
            observer.handle(body)
        if not self.no_ack:
            self.acknowledge_message(basic_deliver.delivery_tag)

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.
        """

        self._channel.basic_ack(delivery_tag)

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.
        """

        if self._channel:
            self._channel.basic_cancel(
                consumer_tag=self._consumer_tag,
                callback=self.on_cancelok
            )

    def on_cancelok(self, unused_frame):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.
        """

        self.close_channel()

    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.
        """

        self._channel.close()

    def run(self):
        """Run the example consumer by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the SelectConnection to operate.
        """

        self._connection = self.connect()
        self._connection.ioloop.run_forever()

    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.
        """

        self._closing = True
        self.stop_consuming()
        self._connection.ioloop.stop()

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""

        self._connection.close()
