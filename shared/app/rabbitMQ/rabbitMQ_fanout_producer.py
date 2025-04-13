# -*- coding: utf-8 -*-
import pika
import time
import logging

class RabbitMQProducerFanout:
    def __init__(self, link, port, user_name, password, exchange_fanout, queue_name_kpi, queue_name_frontend, heartbeat=60, blocked_connection_timeout=300):
        self.link = link
        self.port = port
        self.userName = user_name
        self.password = password
        self.exchangeFanout = exchange_fanout
        self.queueNameKpi = queue_name_kpi
        self.queueNameFrontend = queue_name_frontend
        credentials = pika.PlainCredentials(self.userName,self.password)
        self.connection_params = pika.ConnectionParameters(
            self.link,self.port,'/',credentials,
            heartbeat=heartbeat,
            blocked_connection_timeout=blocked_connection_timeout
        )
        self.connection = None
        self.channel = None

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(self.connection_params)
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange=self.exchangeFanout,durable=True,
                                          exchange_type='fanout')
            self.channel.queue_declare(queue=self.queueNameKpi,durable=True,arguments={'x-queue-mode': 'lazy'})
            self.channel.queue_declare(queue=self.queueNameFrontend, durable=True, arguments={'x-queue-mode': 'lazy'})
            self.channel.queue_bind(exchange=self.exchangeFanout,queue=self.queueNameKpi)
            self.channel.queue_bind(exchange=self.exchangeFanout,queue=self.queueNameFrontend)
        except Exception as e:
            logging.error(f"Connection Error: {e}, Trying Again...")
            time.sleep(3)
            self.connect()

    def send_message(self,message):
        try:
            self.connect()
            self.channel.basic_publish(exchange=self.exchangeFanout,
                                       routing_key="",
                                       body=message)
            #logging.info(f"[x] Sending Message: {message}")
        except Exception as e:
            logging.critical(f"Sending Message Error: {e}, Reconnection Again...")
            self.reconnect()

    def reconnect(self):
        self.close_connection()
        time.sleep(3)
        self.connect()

    def close_connection(self):
        if self.channel is not None and self.channel.is_open:
            self.channel.close()
        if self.connection is not None and self.connection.is_open:
            self.connection.close()
        logging.info("Conneciton Closed")