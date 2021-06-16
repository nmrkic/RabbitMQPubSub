from unittest import TestCase
from rabbitmqpubsub import rabbit_pubsub


class SubsHandler():
    results = []

    def handle(self, body):
        self.results.append(body)


class SubscriberTest(TestCase):

    def test_subscriber(self):

        amqp_url = "amqp://guest:guest@127.0.0.1:5672/guest"
        subscriber = rabbit_pubsub.Subscriber(
            amqp_url=amqp_url,
            exchange="some",
            exchange_type="direct",
            queue="somequeue",
        )
        test_handler = SubsHandler()
        subscriber.subscribe(test_handler)
        subscriber.start()

        for i in range(10):
            rabbit_pubsub.Publisher(amqp_url).publish_message(
                data={"request_number": i},
                destination="some",
                source="someother"
            )
        subscriber.stop_consuming()
        subscriber.join()
        # print(subscriber._observers[0])
        self.assertEqual(len(test_handler.results), 1)
