import pika
import json
import time
import settings
from settings import logger


class Queue:

    # declare all the queues names in this var
    QUEUES = ['default', 'test']

    def __init__(self, host=settings.RABBIT["host"],
                 port=settings.RABBIT["port"], user=settings.RABBIT["user"],
                 passw=settings.RABBIT["passw"], json_serial=True):
        self.json_serial = json_serial

        credentials = pika.PlainCredentials(user, passw)
        parameters = pika.ConnectionParameters(host, port, '/', credentials)

        self.conn = pika.BlockingConnection(
            pika.ConnectionParameters(host=host))
        self.channel = self.conn.channel()
        for queue in self.QUEUES:
            self.channel.queue_declare(
                queue=queue, arguments={'x-max-priority': 10})

    def __del__(self):
        self.conn.close()

    @staticmethod
    def _valid_queue_(name):
        if name not in Queue.QUEUES:
            raise ValueError('Undeclared queue name used: %s' % name)

    @staticmethod
    def _encode(body):
        return json.dumps(body)

    @staticmethod
    def _decode(body):
        return json.loads(body)

    def add(self, queue='default', body=None, priority=1):
        self._valid_queue_(queue)
        if body:
            if self.json_serial:
                body = self._encode(body)
            self.channel.basic_publish(
                exchange='', routing_key=queue, body=body,
                properties=pika.BasicProperties(priority=priority))

    def purge(self, queue):
        self._valid_queue_(queue)
        self.channel.queue_purge(queue)

    def get_message_count(self, queue):
        self._valid_queue_(queue)
        queue = self.channel.queue_declare(
            queue=queue, arguments={'x-max-priority': 10})
        return int(queue.method.message_count)


class QueueConsumer(Queue):

    RECONNECTION_DELAY = 3

    def __init__(self, queue='default', *args, **kwargs):
        while True:
            try:
                super(QueueConsumer, self).__init__(*args, **kwargs)
                self.channel.basic_consume(
                    queue=queue, on_message_callback=self.callback,
                    auto_ack=True)
                print(' [*] Waiting for messages. To exit press CTRL+C')
                self.channel.start_consuming()
            # Don't recover if connection was closed by broker
            except pika.exceptions.ConnectionClosedByBroker as ex:
                logger.exception(ex)
                break
            # Don't recover on channel errors
            except pika.exceptions.AMQPChannelError as ex:
                logger.exception(ex)
                break
            # Recover on all other connection errors
            except pika.exceptions.AMQPConnectionError as ex:
                logger.exception(ex)
                time.sleep(self.RECONNECTION_DELAY)
                continue

    @staticmethod
    def callback(ch, method, properties, body):
        body = Queue._decode(body)
        print(" [x] Received %r" % body)
