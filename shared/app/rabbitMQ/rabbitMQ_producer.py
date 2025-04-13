# -*- coding: utf-8 -*-
import pika
import time
import logging

class RabbitMQProducer:
    def __init__(self,link,port,user_name,password,heartbeat=60, blocked_connection_timeout=300):
        self.link = link
        self.port = port
        self.userName = user_name
        self.password = password
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
        except Exception as e:
            logging.error(f"Connection Error: {e}, Trying Again...")
            time.sleep(3)
            self.connect()

    def send_message(self,message,exchange):
        try:
            self.connect()
            self.channel.basic_publish(exchange=exchange,
                                       routing_key="#",
                                       body=message,
                                       properties=pika.BasicProperties(expiration='300000'))
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