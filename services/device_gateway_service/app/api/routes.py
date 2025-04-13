from fastapi import APIRouter
from shared.app.enums import UserType, UserInfoType, UserTestType, TopicRemoveUserModel, UserCloseListenModel
import uuid
from fastapi import Depends,HTTPException,Security
from services.device_gateway_service.app.core.config import API_KEY
from starlette.status import HTTP_403_FORBIDDEN
from fastapi.security.api_key import APIKeyHeader
from services.device_gateway_service.app.queue import task_queue

router = APIRouter()
api_key_header = APIKeyHeader(name="api_key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Invalid API Key"
        )


@router.post('/gateway/topic-listen')
def add_user(user: UserType, api_key: str = Depends(verify_api_key)):
    user.main_task_id = str(uuid.uuid4())
    task_queue.put({"source": "gateway/topic-listen", "data": user})
    return {"status": "User Listen job add queue", UserInfoType.main_task_id.name: user.main_task_id}


@router.post('/gateway/test-topic-listen')
def add_test_user(user: UserTestType, api_key: str = Depends(verify_api_key)):
    user.main_task_id = str(uuid.uuid4())
    task_queue.put({"source": "gateway/test-topic-listen", "data": user})
    return {"status": "User Test Listen job add queue", UserInfoType.main_task_id.name: user.main_task_id}


@router.put('/gateway/topic-remove')
def topic_remove(remove_user: TopicRemoveUserModel, api_key: str = Depends(verify_api_key)):
    task_queue.put({"source": "gateway/topic-remove", "data": remove_user})
    return {"status": "Topic Remove job add queue", UserInfoType.sub_task_id.name: remove_user.sub_task_id}


@router.put('/gateway/topic-listen-close')
def topic_listen_close(user: UserCloseListenModel, api_key: str = Depends(verify_api_key)):
    user.main_task_id = str(uuid.uuid4())
    task_queue.put({"source": "gateway/topic-listen-close", "data": user})
    return {"status": "Topic Listen Close job add queue", UserInfoType.main_task_id.name: user.main_task_id}