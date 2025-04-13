from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP, func

Base = declarative_base()

class TaskState(Base):
    __tablename__ = "task_states"
    __table_args__ = {'schema': 'mm_device'}
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100))
    create_time = Column(TIMESTAMP(timezone=True), default=func.now())
    main_task_action = Column(String(100))
    sub_task_action = Column(String(100))
    main_task_id = Column(String(100))
    sub_task_id = Column(String(100))
    next_task_id = Column(String(100))