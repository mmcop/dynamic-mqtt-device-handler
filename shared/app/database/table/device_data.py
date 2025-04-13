from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP, func

Base = declarative_base()

class DeviceData(Base):
    __tablename__ = "device_data"
    __table_args__ = {'schema': 'mm_device'}
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    data = Column(JSON)
    topic = Column(String(100))
    timestamp = Column(TIMESTAMP(timezone=True), default=func.now())
    error = Column(Integer)
    error_log = Column(String(100))