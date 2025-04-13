# -*- coding: utf-8 -*-
import pika
import time
import json
import logging
from services.device_alarm_service.app.services.alarm_control_service import alarm_control

class RabbitMQConsumerAlarm:
    def __init__(self, link,port,userName,password):
        self.link = link
        self.port = port
        self.userName = userName
        self.password = password
        credentials = pika.PlainCredentials(self.userName,self.password)
        self.connection_params = pika.ConnectionParameters(
            self.link,self.port,'/',credentials
        )
        self.connection = None
        self.channel = None
    def connect(self,queueName):
        """RabbitMQ sunucusuna bağlan ve bir kanal oluştur."""
        try:
            self.connection = pika.BlockingConnection(self.connection_params)
            self.channel = self.connection.channel()

        except Exception as e:
            logging.error(f"Connection Error: {e}, Trying Again...")
            time.sleep(3)
            self.reconnect(queueName)

    def consume(self,queueName):
        """Mesajları tüketmeye başla."""
        self.connect(queueName)
        self.channel.basic_consume(
            queue=queueName,
            on_message_callback=self.on_message,
            auto_ack=True
        )
        logging.info(f'{queueName} [*] Listening Queue')
        try:
            self.channel.start_consuming()
        except Exception as e:
            logging.error(f"Connection Error: {e}, Trying Again...")
            self.reconnect(queueName)
        except KeyboardInterrupt:
            self.close_connection()

    def on_message(self, ch, method, properties, body):
        """Mesaj alındığında çağrılır."""
        try:
            message = json.loads(body.decode('utf-8'))
            logging.info(f"[x] Received Message: {message}")
            alarm_control(message)
        except Exception as e:
            logging.error("RabbitMQ consumer alarm error: "+e)

    def reconnect(self,queueName):
        """Bağlantıyı yeniden kur."""
        self.close_connection()
        time.sleep(3)
        self.consume(queueName)

    def close_connection(self):
        """Bağlantıyı kapat."""
        if self.channel is not None and self.channel.is_open:
            self.channel.close()
        if self.connection is not None and self.connection.is_open:
            self.connection.close()
        logging.info("Connection Closed")