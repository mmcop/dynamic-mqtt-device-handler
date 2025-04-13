# -*- coding: utf-8 -*-
import pika
import time
import json
from shared.app.enums.message_type import MessageType
from shared.app.database.table import DeviceData
import logging

class RabbitMQConsumer:
    def __init__(self, link,port,userName,password,exchangeName,pgclient):
        self.link = link
        self.port = port
        self.userName = userName
        self.password = password
        self.exchangeName = exchangeName
        self.pgclient = pgclient
        credentials = pika.PlainCredentials(self.userName,self.password)
        self.connection_params = pika.ConnectionParameters(
            self.link,self.port,'/',credentials
        )
        self.connection = None
        self.channel = None
    def connect(self,queueName,exchangeName,deadLetterExchange=None):
        """RabbitMQ sunucusuna bağlan ve bir kanal oluştur."""
        try:
            self.connection = pika.BlockingConnection(self.connection_params)
            self.channel = self.connection.channel()
            if deadLetterExchange is None:
                self.channel.queue_declare(queue=queueName, durable=True)
                self.channel.exchange_declare(exchange=exchangeName,
                                              exchange_type='topic',
                                              durable=True)

            else:
                self.channel.queue_declare(queue=queueName,durable=True,arguments={'x-dead-letter-exchange': deadLetterExchange,
                                                                                         'x-dead-letter-routing-key': '#',
                                                                                   'x-delayed-type': 'headers',
                                                                                   'x-queue-mode': 'lazy'})
                self.channel.exchange_declare(exchange=exchangeName,
                                          exchange_type='x-delayed-message',
                                          durable=True,
                                          arguments={'x-delayed-type': 'topic'})

            self.channel.queue_bind(queue=queueName, exchange=exchangeName,
                                         routing_key ="#")
        except Exception as e:
            logging.error(f"Connection Error: {e}, Trying Again...")
            time.sleep(3)
            self.reconnect(queueName,exchangeName,deadLetterExchange)

    def consume(self,queueName,exchangeName,deadLetterExchange=None):
        """Mesajları tüketmeye başla."""
        self.connect(queueName,exchangeName,deadLetterExchange)
        self.channel.basic_consume(
            queue=queueName,
            on_message_callback=self.on_message,
            auto_ack=False
        )
        logging.info(f'{queueName} [*] Listening Queue')
        try:
            self.channel.start_consuming()
        except Exception as e:
            logging.error(f"Connection Error: {e}, Trying Again...")
            self.reconnect(queueName,exchangeName,deadLetterExchange)
        except KeyboardInterrupt:
            self.close_connection()

    def on_message(self, ch, method, properties, body):
        """Mesaj alındığında çağrılır."""
        global message
        try:
            message = json.loads(body.decode('utf-8'))
            #logging.info(f"[x] Received Message: {message}")
            try:
                self.pgclient.insert_message(table_class=DeviceData, message=message)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                message[MessageType.errorLog.value] = str(e)
                self.handle_message_failure(ch, method, message)
        except Exception as e:
            message[MessageType.errorLog.value] = str(e)
            self.handle_message_failure(ch, method, message)

    def handle_message_failure(self, ch, method, message):
        try:
            if message[MessageType.error.value] <= 3:
                message[MessageType.error.value] += 1
                logging.warning(f"Message will be retried, error count: {message[MessageType.error.value]}")
                ch.basic_publish(
                    exchange=self.exchangeName,
                    routing_key='#',
                    body=json.dumps(message),
                    properties=pika.BasicProperties(headers={'x-delay': 5000})
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                logging.critical(f"Message failed after multiple attempts: {message}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as publish_exception:
            logging.critical(f"Failed to retry message: {publish_exception}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def reconnect(self,queueName,exchangeName,deadLetterExchange):
        """Bağlantıyı yeniden kur."""
        self.close_connection()
        time.sleep(3)
        self.consume(queueName,exchangeName,deadLetterExchange)

    def close_connection(self):
        """Bağlantıyı kapat."""
        if self.channel is not None and self.channel.is_open:
            self.channel.close()
        if self.connection is not None and self.connection.is_open:
            self.connection.close()
        self.pgclient.close_connection()
        logging.info("Connection Closed")