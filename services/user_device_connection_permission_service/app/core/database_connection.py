from shared.app.database.client import PostgreSQLORMClient
from services.user_device_connection_permission_service.app.core.config import DATABASE_HOST, DATABASE_PORT, DATABASE_NAME, DATABASE_USERNAME, DATABASE_PASSWORD

pg_client = PostgreSQLORMClient(
        host=DATABASE_HOST,
        port=DATABASE_PORT,
        dbname=DATABASE_NAME,
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD,
        check_health=False,
        health_check_interval=60,
        pool_size=2
    )

def start_connection():
    pg_client.connect()

def close_connection():
    pg_client.close_connection()