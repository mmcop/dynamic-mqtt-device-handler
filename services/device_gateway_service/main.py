from fastapi import FastAPI
import threading
from services.device_gateway_service.app.queue import worker
from services.device_gateway_service.app.api import router
import uvicorn
from services.device_gateway_service.app.core.config import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, ELASTICSEARCH_CONNECTION
from services.device_gateway_service.app.services import freeClient, basicClient, premiumClient, testConnectionClient, delete_mqtt_and_thread_object
from services.device_gateway_service.app.core.database_connection import start_connection, close_connection, pull_old_user
from shared.app.enums.general_type import GeneralType
from shared.app.utils import setup_logging
import logging

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
def on_startup():
    start_connection()

@app.on_event("shutdown")
def on_shutdown():
    logger.info("Gateway MQTT Service Closing...")
    if freeClient:
        delete_mqtt_and_thread_object(freeClient)
    if basicClient:
        delete_mqtt_and_thread_object(basicClient)
    if premiumClient:
        delete_mqtt_and_thread_object(premiumClient)
    if testConnectionClient:
        testConnectionClient[GeneralType.mqtt_client_object.name].disconnect()
        testConnectionClient[GeneralType.thread_object.name].shutdown()
    logging.info("All MQTT clients disconnected")
    close_connection()

if __name__ == "__main__":
    logger = setup_logging('device_gateway_service',[{'host': ELASTICSEARCH_HOST, 'port': ELASTICSEARCH_PORT, 'scheme': 'http'}],es_start=ELASTICSEARCH_CONNECTION, index_name='mm-device-gateway-service')
    logger.info("Gateway MQTT Service Starting...")

    gateway_old_user = pull_old_user()

    worker_thread = threading.Thread(target=worker,args=(gateway_old_user,),name="gateway_worker_thread", daemon=True)
    worker_thread.start()

    uvicorn.run(app, host="0.0.0.0", port=5001, reload=False)