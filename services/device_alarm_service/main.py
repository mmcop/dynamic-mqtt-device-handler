from services.device_alarm_service.app.core.config import RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASSWORD, AMQP_PORT, QUEUE_NAME, ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, ELASTICSEARCH_CONNECTION
from shared.app.utils import setup_logging

logger = setup_logging('device_alarm_service',[{'host': ELASTICSEARCH_HOST, 'port': ELASTICSEARCH_PORT, 'scheme': 'http'}],es_start=ELASTICSEARCH_CONNECTION, index_name='mm-device-gateway-service')
logger.info("Alarm Service Starting...")

from shared.app.database.client import PostgreSQLORMClientSingle
from services.device_alarm_service.app.core.config import DATABASE_HOST,DATABASE_PORT,DATABASE_NAME,DATABASE_USERNAME,DATABASE_PASSWORD
from shared.app.database.table import  AlarmDefinitions, AlarmRules, LogicGroups
from services.device_alarm_service.app.services.redis_conneciton import RedisConnection
import redis
import json

pg_client = PostgreSQLORMClientSingle( host=DATABASE_HOST,
        port=DATABASE_PORT,
        dbname=DATABASE_NAME,
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
        pool_size=1)

pg_client.connect()
pg_client.create_table(table_class=AlarmDefinitions)
pg_client.create_table(table_class=LogicGroups)
pg_client.create_table(table_class=AlarmRules)

redis_connection = RedisConnection()

def load_initial_cache():
    """Uygulama başlangıcında cache'i yükler."""
    with pg_client.SessionLocal() as session:
        # Alarm Definitions Cache
        alarms = session.query(AlarmDefinitions).filter(AlarmDefinitions.active == True).filter((AlarmDefinitions.active == True)).all()
        for alarm in alarms:
            cache_key = f"alarm:{alarm.topic}"
            redis_connection.redis_client.set(cache_key, json.dumps(alarm.to_dict()))

        # Logic Groups Cache
        logic_groups = session.query(LogicGroups).all()
        for group in logic_groups:
            cache_key = f"logic_group:{group.id}"
            redis_connection.redis_client.set(cache_key, json.dumps(group.to_dict()))

        # Alarm Rules Cache
        rules = session.query(AlarmRules).all()
        for rule in rules:
            cache_key = f"rule:{rule.id}"
            redis_connection.redis_client.set(cache_key, json.dumps(rule.to_dict()))

try:
    if redis_connection.redis_client.ping():
        load_initial_cache()
        print("Redis bağlantısı başarılı ve sağlıklı.")
except redis.ConnectionError as e:
    print(f"Redis bağlantı hatası: {e}")



CACHE_UPDATE_CHANNEL = "cache_update"

def cache_update_worker():
    """Redis Pub/Sub ile gelen mesajları dinler ve cache'i günceller."""
    pubsub = redis_connection.redis_client.pubsub()
    pubsub.subscribe(CACHE_UPDATE_CHANNEL)

    for message in pubsub.listen():
        if message['type'] == 'message':
            event = json.loads(message['data'])
            handle_cache_event(event)

def handle_cache_event(event):
    """Cache güncellenmesi için gelen olayları işler."""
    if event['type'] == "alarm_update":
        alarm = event['data']
        cache_key = f"alarms:{alarm['topic']}"
        redis_connection.redis_client.set(cache_key, json.dumps(alarm))

    elif event['type'] == "alarm_delete":
        cache_key = f"alarms:{event['id']}"
        redis_connection.redis_client.delete(cache_key)

import threading
worker_thread = threading.Thread(target=cache_update_worker, daemon=True)
worker_thread.start()

from shared.app.rabbitMQ.rabbitmq_consumer_alarm import RabbitMQConsumerAlarm

message_consumer = RabbitMQConsumerAlarm(link=RABBITMQ_HOST, password=RABBITMQ_PASSWORD, userName=RABBITMQ_USER, port=AMQP_PORT)
message_consumer.consume(queueName=QUEUE_NAME)