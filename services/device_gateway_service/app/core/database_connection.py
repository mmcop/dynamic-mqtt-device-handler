from shared.app.database.client import PostgreSQLORMClient
from shared.app.rabbitMQ.rabbitMQ_fanout_producer import RabbitMQProducerFanout
from services.device_gateway_service.app.core.config import DATABASE_HOST, DATABASE_PORT, DATABASE_NAME, DATABASE_USERNAME, DATABASE_PASSWORD, RABBITMQ_HOST, RABBITMQ_PASSWORD, RABBITMQ_USER, EXCHANGE_FANOUT, QUEUE_KPI, QUEUE_FRONTEND, AMQP_PORT
from shared.app.enums.user_type import UserType
from shared.app.database.table import TaskState
import uuid

pg_client = PostgreSQLORMClient(
        host=DATABASE_HOST,
        port=DATABASE_PORT,
        dbname=DATABASE_NAME,
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
        check_health=False,
        health_check_interval=60,
        pool_size=1
    )

def start_connection():
    pg_client.connect()
    pg_client.create_table(table_class=TaskState)
    producer_initialize = RabbitMQProducerFanout(link=RABBITMQ_HOST, exchange_fanout=EXCHANGE_FANOUT, password=RABBITMQ_PASSWORD, port=AMQP_PORT, user_name=RABBITMQ_USER, queue_name_kpi=QUEUE_KPI, queue_name_frontend=QUEUE_FRONTEND)
    producer_initialize.connect()
    producer_initialize.close_connection()

def close_connection():
    pg_client.close_connection()

def pull_old_user():
    results, table = pg_client.select_from_table(table_name="device_connection_definition", schema="mm_device")
    parsed_results = pg_client.parse_results_to_model(results, table)
    old_user_list = []
    for item in parsed_results:
        if item.active:
            old_user_list.append(UserType(
                username=item.username_prefix + item.username,
                password=item.password,
                topic=item.tenant_id+"/"+item.topic,
                company=item.tenant_id,
                max_messages_per_minute=item.max_messages_per_min,
                max_message_size=item.max_message_size,
                subscribe_type=item.subscription_type,
                main_task_id=str(uuid.uuid4())))
    return old_user_list
