from unittest import TestCase
from rabbitmqpubsub import rabbit_pubsub
import time
import datetime as dt
import logging


logger = logging.getLogger(__name__)


class SubsHandler:
    results = {}

    def handle(self, body):
        amqp_url = "amqp://guest:guest@127.0.0.1:5672/guest"
        test = body.get("data", {}).get("test")
        if test:
            if test not in self.results.keys():
                self.results[body["data"]["test"]] = []
            self.results[body["data"]["test"]].append(body)
        rabbit_pubsub.Publisher(amqp_url).publish_message(
            data=body["data"],
            destination=body["meta"]["source"],
            source="subscriber",
            corr_id=body["meta"]["correlationId"],
        )
        return body["data"]


class SubscriberTest(TestCase):
    def setUp(self):
        self.test_handler = SubsHandler()

    def tearDown(self):
        self.test_handler.results = []

    def test_subscriber_async(self):
        amqp_url = "amqp://guest:guest@127.0.0.1:5672/guest"
        subscriber = rabbit_pubsub.Subscriber(
            amqp_url=amqp_url,
            exchange="subscriber",
            exchange_type="direct",
            queue="somequeue",
            async_processing=True,
        )
        subscriber.subscribe(self.test_handler)
        subscriber.start()

        for i in range(10):
            rabbit_pubsub.Publisher(amqp_url).publish_message(
                data={"request_number": i, "test": "b"},
                destination="subscriber",
                source="source",
            )
        time.sleep(2)
        subscriber.stop_consuming()
        subscriber.join()
        for a in self.test_handler.results["b"]:
            logger.info(f"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa {a}")
        self.assertEqual(len(self.test_handler.results["b"]), 10)
        self.test_handler.results = []

    def test_dateconversion(self):
        amqp_url = "amqp://guest:guest@127.0.0.1:5672/guest"
        subscriber = rabbit_pubsub.Subscriber(
            amqp_url=amqp_url,
            exchange="some",
            exchange_type="direct",
            queue="somequeue",
            async_processing=True,
        )
        subscriber.subscribe(self.test_handler)
        subscriber.start()

        rpc = rabbit_pubsub.RpcClient(
            amqp_url=amqp_url,
            exchange="rpc",
            queue="rpcqueue",
        )
        data = {"test_date": dt.datetime.now()}
        return_data = rpc.call(data, recipient="subscriber")
        subscriber.stop_consuming()
        subscriber.join()
        self.test_handler.results = []
        self.assertEqual(data, return_data["data"])

    def test_dateonlyconversion(self):
        amqp_url = "amqp://guest:guest@127.0.0.1:5672/guest"
        subscriber = rabbit_pubsub.Subscriber(
            amqp_url=amqp_url,
            exchange="some",
            exchange_type="direct",
            queue="somequeue",
            async_processing=True,
        )
        subscriber.subscribe(self.test_handler)
        subscriber.start()

        rpc = rabbit_pubsub.RpcClient(
            amqp_url=amqp_url,
            exchange="rpc",
            queue="rpcqueue",
        )
        data = {"test_date": dt.datetime.now().date()}
        return_data = rpc.call(data, recipient="subscriber")
        subscriber.stop_consuming()
        subscriber.join()
        self.test_handler.results = []
        self.assertEqual(data, return_data["data"])

    def test_send_bytes(self):
        amqp_url = "amqp://guest:guest@127.0.0.1:5672/guest"
        subscriber = rabbit_pubsub.Subscriber(
            amqp_url=amqp_url,
            exchange="some",
            exchange_type="direct",
            queue="somequeue",
            async_processing=True,
        )
        subscriber.subscribe(self.test_handler)
        subscriber.start()

        rpc = rabbit_pubsub.RpcClient(
            amqp_url=amqp_url,
            exchange="rpc",
            queue="rpcqueue",
        )
        data = {"test_bytes": {"test_bytes": b"This is a bytes string"}}
        return_data = rpc.call(data, recipient="subscriber")
        subscriber.stop_consuming()
        subscriber.join()
        self.test_handler.results = []
        self.assertEqual(data, return_data["data"])
