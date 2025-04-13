from fastapi import APIRouter
from shared.app.enums import UserType, UserInfoType, UserUpdateModel
import uuid
from fastapi import Depends,HTTPException,Security
from services.user_device_connection_permission_service.app.core.config import API_KEY
from starlette.status import HTTP_403_FORBIDDEN
from fastapi.security.api_key import APIKeyHeader
from services.user_device_connection_permission_service.app.queue import task_queue

router = APIRouter()
api_key_header = APIKeyHeader(name="api_key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Invalid API Key"
        )

@router.post("/user/create")
def api_create_user(user: UserType, api_key: str = Depends(verify_api_key)):
    user.main_task_id = str(uuid.uuid4())
    task_queue.put({"source": "user/create", "data": user})
    return {"status": "Create User job add queue", UserInfoType.main_task_id.name: user.main_task_id}

@router.put("/user/update")
def update_user(user: UserUpdateModel, api_key: str = Depends(verify_api_key)):
    user.old_user_topic.main_task_id = str(uuid.uuid4())
    user.new_user_topic.main_task_id = user.old_user_topic.main_task_id
    task_queue.put({"source": "user/update", "data": user})
    return {"status": "Update User job add queue", UserInfoType.main_task_id.name: user.new_user_topic.main_task_id}

@router.put("/user/delete")
def api_delete_user(user: UserType, api_key: str = Depends(verify_api_key)):
    user.main_task_id = str(uuid.uuid4())
    task_queue.put({"source": "user/delete", "data": user})
    return {"status": "Delete User job add queue", UserInfoType.main_task_id.name: user.main_task_id}