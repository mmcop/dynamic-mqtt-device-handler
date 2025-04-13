import os

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')
MQTT_PORT = int(os.getenv('MQTT_PORT',"1883"))
EXCHANGE_NAME = os.getenv('EXCHANGE_NAME')
AMQP_PORT = int(os.getenv('AMQP_PORT',"5672"))
EXCHANGE_FANOUT = os.getenv('EXCHANGE_FANOUT')
QUEUE_KPI = os.getenv('QUEUE_KPI')
QUEUE_FRONTEND = os.getenv('QUEUE_FRONTEND')
ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST')
ELASTICSEARCH_CONNECTION = True if os.getenv('ELASTICSEARCH_CONNECTION') == "True" else False
ELASTICSEARCH_PORT = int(os.getenv('ELASTICSEARCH_PORT'))
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_PORT = int(os.getenv('DATABASE_PORT',"5432"))
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
API_KEY = os.getenv('API_KEY')
MQTT_TIMEOUT = 300
FREE_THREAD_WORKER = 1
BASIC_THREAD_WORKER = 1
PREMIUM_THREAD_WORKER = 1
freeChunkSize = 200
basicChunkSize = 100
freeThreadName = 'free_listen_thread'
basicThreadName = 'basic_listen_thread'
subTaskListenTopic = "listen_topic_"
subTaskControlTopic = "control_topic_"
subTaskTestTopic = "test_topic_"
subTaskCloseListenTopic = "close_listen_topic_"