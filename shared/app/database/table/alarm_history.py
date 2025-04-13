from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP, func

Base = declarative_base()

class AlarmHistory(Base):
    __tablename__ = "alarm_history"
    __table_args__ = {'schema': 'mm_device'}
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    triggered_at = Column(TIMESTAMP(timezone=True), default=func.now())
    sensor_data = Column(JSON)
    action_taken = Column(String(255))
    status = Column(String(50))