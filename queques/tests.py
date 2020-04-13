import unittest
from queques import Queue, QueueConsumer
import pika
import time


class TestQueueMethods(unittest.TestCase):

    def setUp(self) -> None:
        self.queue = Queue()
        self.queue.purge("default")

    def test_add_count(self):
        self.assertEqual(self.queue.get_message_count("default"), 0)
        test_data = {"t1": 11}
        self.queue.add(body=test_data)
        time.sleep(0.2)
        self.assertEqual(self.queue.get_message_count("default"), 1)
        method_frame, header_frame, body = self.queue.channel.basic_get('default', auto_ack=True)
        self.assertEqual(self.queue._decode(body), test_data)
        self.assertEqual(self.queue.get_message_count("default"), 0)


class TestQueueConsumer(unittest.TestCase):

    def setUp(self) -> None:
        self.queue = Queue()
        self.queue.purge("default")

    def test_consumer(self):
        class QTest(QueueConsumer):

            @staticmethod
            def callback(ch, method, properties, body):
                assert QTest._decode(body) == {"t1": 11}
                raise pika.exceptions.ConnectionClosedByBroker("0", "Test")

        self.assertEqual(self.queue.get_message_count("default"), 0)
        test_data = {"t1": 11}
        self.queue.add(body=test_data)
        time.sleep(0.2)
        self.assertEqual(self.queue.get_message_count("default"), 1)
        QTest()
        self.assertEqual(self.queue.get_message_count("default"), 0)


if __name__ == '__main__':
    unittest.main()
