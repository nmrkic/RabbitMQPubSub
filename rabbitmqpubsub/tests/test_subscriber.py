from unittest import TestCase
from rabbitmqpubsub import rabbit_pubsub
import json
import time


class SubsHandler():
    results = {}

    def handle(self, body):
        body = json.loads(body)
        print(body)
        if body.get("data", {}).get("test") not in self.results.keys():
            self.results[body['data']['test']] = []
        self.results[body['data']['test']].append(body)


class SubscriberTest(TestCase):

    def setUp(self):
        self.test_handler = SubsHandler()

    def tearDown(self):
        self.test_handler.results = []

    def test_subscriber_async(self):

        amqp_url = "amqp://guest:guest@127.0.0.1:5672/guest"
        subscriber = rabbit_pubsub.Subscriber(
            amqp_url=amqp_url,
            exchange="someother",
            exchange_type="direct",
            queue="somequeue",
        )
        subscriber.subscribe(self.test_handler)
        subscriber.start()

        for i in range(10):
            rabbit_pubsub.Publisher(amqp_url).publish_message(
                data={"request_number": i, "test": "b"},
                destination="some",
                source="someother"
            )
        time.sleep(2)
        subscriber.stop_consuming()
        subscriber.join()
        # print(subscriber._observers[0])
        self.assertEqual(len(self.test_handler.results["b"]), 10)
        self.test_handler.results = []

    def test_subscriber_block(self):

        amqp_url = "amqp://guest:guest@127.0.0.1:5672/guest"
        subscriber = rabbit_pubsub.Subscriber(
            amqp_url=amqp_url,
            exchange="someother",
            exchange_type="direct",
            queue="somequeueother",
            async_processing=False
        )
        subscriber.subscribe(self.test_handler)
        subscriber.start()

        for i in range(20):
            rabbit_pubsub.Publisher(amqp_url).publish_message(
                data={"request_number": i, "test": "a"},
                destination="some",
                source="someother",
            )
        time.sleep(2)
        subscriber.stop_consuming()
        subscriber.join()
        # print(subscriber._observers[0])
        self.assertEqual(len(self.test_handler.results["a"]), 20)
        self.test_handler.results = []
