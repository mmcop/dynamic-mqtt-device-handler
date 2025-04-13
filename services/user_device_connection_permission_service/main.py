from fastapi import FastAPI
from services.user_device_connection_permission_service.app.api import router
from shared.app.utils.logging_config import setup_logging
from services.user_device_connection_permission_service.app.core.config import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, ELASTICSEARCH_CONNECTION
from services.user_device_connection_permission_service.app.queue import worker
from services.user_device_connection_permission_service.app.core.database_connection import start_connection, close_connection
import uvicorn
import threading

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
def on_startup():
    start_connection()

@app.on_event("shutdown")
def on_shutdown():
    logger.info("RabbitMQ Create User and Permission Service Closing...")
    close_connection()

if __name__ == '__main__':
    logger = setup_logging('user_device_connection_permission_service',[{'host': ELASTICSEARCH_HOST, 'port': ELASTICSEARCH_PORT, 'scheme': 'http'}], es_start=ELASTICSEARCH_CONNECTION, index_name='mm-user-device-connection-permission-service')
    logger.info("RabbitMQ Create User and Permission Service Starting...")

    worker_thread = threading.Thread(target=worker,name="user_permission_thread", daemon=True)
    worker_thread.start()

    uvicorn.run(app, host='0.0.0.0', port=5000, reload=False)