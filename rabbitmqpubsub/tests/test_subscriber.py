from unittest import TestCase
from rabbitmqpubsub import rabbit_pubsub


class TestHandler():
    def handle(self):
        print("test")


class SubscriberTest(TestCase):
    def test_subscriber(self):
        subscriber = rabbit_pubsub.Subscriber(
            amqp_url="amqp://some:some@127.0.0.1:5672/some",
            exchange="some",
            exchange_type="direct",
            queue="somequeue",
        )
        subscriber.deamon = True
        subscriber.subscribe(TestHandler())
        subscriber.start()
