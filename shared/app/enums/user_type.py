# -*- coding: utf-8 -*-
from pydantic import BaseModel
from enum import Enum,auto

class UserType(BaseModel):
    username: str
    password: str
    topic: str
    company: str
    max_messages_per_minute: int
    max_message_size: int
    subscribe_type: str
    main_task_id: str
    
class UserTestType(BaseModel):
    username: str
    password: str
    topic: str
    main_task_id: str

class TopicRemoveUserModel(BaseModel):
    sub_task_id: str
    user: UserType

class UserUpdateModel(BaseModel):
    old_user_topic: UserType
    new_user_topic: UserType
    
class UserCloseListenModel(BaseModel):
    username: str
    company: str
    topic: str
    main_task_id: str
    subscribe_type: str

class UserInfoType(Enum):
    max_messages_per_minute = auto()
    max_message_size = auto()
    company = auto()
    topic = auto()
    main_task_id = auto()
    sub_task_id = auto()
    save_database = auto()