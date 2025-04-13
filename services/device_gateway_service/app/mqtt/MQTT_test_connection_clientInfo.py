# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
import time
import logging
import threading
from shared.app.database.table.device_test_connection import DeviceTestConnectionData


class MQTTTestConnectionClient:
    def __init__(self, topicInfo, RABBITMQ_USER, RABBITMQ_PASSWORD, pg_client):
        self.topicInfo = topicInfo  # {topic_name: start_time}
        self.client = mqtt.Client(userdata=topicInfo)
        self.client.username_pw_set(RABBITMQ_USER, RABBITMQ_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.pg_client = pg_client
        self.stop_thread = False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.client.subscribe([(topic, 1) for topic in userdata.keys()])
            logging.info(f"Connected to topics: {list(userdata.keys())} successfully")
        else:
            logging.critical(f"Failed to connect to topics: {list(userdata.keys())}, return code {rc}")

    def on_message(self, client, userdata, msg):
        if msg.topic in self.topicInfo:
            self.pg_client.insert_message(table_class=DeviceTestConnectionData,message= {'topic': msg.topic, 'data': msg.payload.decode('utf-8')})
            self.stop_listening_to_topic(msg.topic)
        else:
            logging.critical(f"Unauthorized messages listening. The topic: {msg.topic}")

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logging.info(f"Unexpected disconnection from topics {list(userdata.keys())}")
            self.client.reconnect()

    def connect(self, RABBITMQ_HOST, MQTT_PORT, MQTT_TIMEOUT):
        try:
            self.client.connect(RABBITMQ_HOST, MQTT_PORT, MQTT_TIMEOUT)
            self.client.loop_start()

            self.timeout_thread = threading.Thread(target=self.check_topic_timeouts)
            self.timeout_thread.start()
        except Exception as e:
            logging.critical(f"Failed to connect to MQTT broker for topics {list(self.topicInfo.keys())}: {e}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.stop_thread = True 
        if self.timeout_thread.is_alive():
            self.timeout_thread.join()
        logging.info(f"Disconnected from topics {list(self.topicInfo.keys())}")

    def reconnect(self):
        try:
            self.client.reconnect()
            logging.info("Reconnected to MQTT broker")
            logging.info(f"Reconnected to MQTT broker for topics {list(self.topicInfo.keys())}")
            
            if not self.timeout_thread.is_alive():
                self.stop_thread = False
                self.timeout_thread = threading.Thread(target=self.check_topic_timeouts)
                self.timeout_thread.start()

        except Exception as e:
            logging.critical(f"Failed to reconnect to MQTT broker for topics {list(self.topicInfo.keys())}: {e}")

    def stop_listening_to_topic(self, topic):
        if topic in self.topicInfo:
            try:
                self.client.unsubscribe(topic)
                del self.topicInfo[topic]
                logging.info(f"Stopped listening to topic: {topic}")
            except Exception as e:
                logging.critical(f"Failed to unsubscribe from topic {topic}: {e}")
        else:
            logging.warning(f"Topic {topic} not found in subscribed topics")

    def check_topic_timeouts(self):
        """Bu fonksiyon belirli aralıklarla topic'lerin zaman aşımını kontrol eder."""
        while not self.stop_thread:
            current_time = time.time()
            topics_to_remove = []

            for topic, start_time in self.topicInfo.items():
                if current_time - start_time >= 300:
                    logging.info(f"Timeout reached for topic: {topic}")
                    topics_to_remove.append(topic)

            for topic in topics_to_remove:
                self.stop_listening_to_topic(topic)

            time.sleep(1)
