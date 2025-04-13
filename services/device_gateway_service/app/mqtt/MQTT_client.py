# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
import time
from shared.app.enums import UserInfoType
from shared.app.enums.general_type import GeneralType
from shared.app.rabbitMQ.rabbitMQ_producer import RabbitMQProducer
from shared.app.rabbitMQ.rabbitMQ_fanout_producer import RabbitMQProducerFanout
from shared.app.enums.message_type import MessageType
from shared.app.database.table import DeviceData
import json
import logging

class MQTTClient:
    def __init__(self, topicInfo, RABBITMQ_USER, RABBITMQ_PASSWORD, RABBITMQ_HOST, AMQP_PORT, EXCHANGE, pg_client, EXCHANGE_FANOUT, QUEUE_KPI, QUEUUE_FRONTEND, client_id):
        self.topicInfo = topicInfo
        self.client = mqtt.Client(client_id=client_id,userdata=topicInfo)
        self.client.username_pw_set(RABBITMQ_USER, RABBITMQ_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.exchange = EXCHANGE
        self.pg_client = pg_client
        self.rabbitMQProducer = RabbitMQProducer(link=RABBITMQ_HOST,port=AMQP_PORT,user_name=RABBITMQ_USER,password=RABBITMQ_PASSWORD)
        self.rabbitMQProducerFanout = RabbitMQProducerFanout(link=RABBITMQ_HOST,port=AMQP_PORT,user_name=RABBITMQ_USER,password=RABBITMQ_PASSWORD,
                                                             exchange_fanout=EXCHANGE_FANOUT,queue_name_kpi=QUEUE_KPI,queue_name_frontend=QUEUUE_FRONTEND)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.client.subscribe([(topic, 1) for topic in userdata.keys()])
            logging.info(f"Connected to topic {userdata.keys()} successfully")
        else:
            logging.critical(f"Failed to connect to topic {userdata.keys()}, return code {rc}")

    def on_message(self, client, userdata, msg):
        if msg.topic in self.topicInfo:
            self.topicInfo[msg.topic][GeneralType.current_time.name] = time.time()
            if GeneralType.start_time.name in self.topicInfo[msg.topic]:
                if(self.topicInfo[msg.topic][GeneralType.current_time.name] - self.topicInfo[msg.topic][GeneralType.start_time.name]) >= 60:
                    self.topicInfo[msg.topic][GeneralType.start_time.name] = self.topicInfo[msg.topic][GeneralType.current_time.name]
                    self.topicInfo[msg.topic][GeneralType.message_count.name] = 0
            else:
                self.topicInfo[msg.topic][GeneralType.start_time.name] = time.time()
                self.topicInfo[msg.topic][GeneralType.message_count.name] = 0
    
            if (GeneralType.message_count.name in self.topicInfo[msg.topic]):
                if (self.topicInfo[msg.topic][GeneralType.message_count.name] < self.topicInfo[msg.topic][UserInfoType.max_messages_per_minute.name] and
                   len(msg.payload) <= self.topicInfo[msg.topic][UserInfoType.max_message_size.name]):
                    self.topicInfo[msg.topic][GeneralType.message_count.name] = self.topicInfo[msg.topic][GeneralType.message_count.name] + 1
                    send_messages = {MessageType.topic.value: msg.topic,
                                     MessageType.data.value: msg.payload.decode('utf-8'),
                                     MessageType.error.value: 0,
                                     MessageType.errorLog.value: ""}
                    self.rabbitMQProducerFanout.send_message(json.dumps(send_messages))
                    if self.topicInfo[msg.topic][UserInfoType.save_database.name]:
                        try:
                            self.rabbitMQProducer.send_message(json.dumps(send_messages), self.exchange)
                        except Exception:
                            self.pg_client.insert_message(table_class=DeviceData,message= send_messages)
                else:
                    logging.info(f"Message ignored for topic {msg.topic} due to rate limit or size limit")
            time.sleep(0.1)
        else:
            logging.critical(f"Unauthorized messages Listening. The Topic: {msg.topic}")

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logging.info(f"Unexpected disconnection from topic {userdata.keys()}")
            self.client.reconnect()

    def connect(self,RABBITMQ_HOST,MQTT_PORT, MQTT_TIMEOUT):
        try:
            self.client.connect(RABBITMQ_HOST, MQTT_PORT, MQTT_TIMEOUT)
            self.client.loop_start()
        except Exception as e:
            logging.critical(f"Failed to connect to MQTT broker for topic {self.topicInfo.keys()}: {e}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        logging.info(f"Disconnected from topic {self.topicInfo.keys()}")

    def reconnect(self):
        try:
            self.client.reconnect()
            logging.info("Reconnected to MQTT broker")
            logging.info(f"Reconnected to MQTT broker for topic {self.topicInfo.keys()}")
        except Exception as e:
            logging.critical(f"Failed to reconnect to MQTT broker for topic {self.topicInfo.keys()}: {e}")
            
    def stop_listening_to_topics(self, topics):
        try:
            self.client.unsubscribe([(topic) for topic in topics])
            logging.info(f"Stopped listening to topics: {topics}")
        except Exception as e:
            logging.critical(f"Failed to unsubscribe from topics {topics}: {e}")