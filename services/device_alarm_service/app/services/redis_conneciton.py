import redis
import json
from shared.app.database.table import  AlarmDefinitions, AlarmRules, LogicGroups
import threading

class RedisConnection:
    _instance = None
    _lock = threading.Lock()
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(RedisConnection,cls).__new__(cls)
        return cls._instance

    def __init__(self):
        pool = redis.ConnectionPool(
            host='localhost',          # Redis sunucusunun adresi
            port=6379,                 # Redis portu
            db=0,                      # Kullanılan veritabanı (varsayılan: 0)
            decode_responses=True,     # Bytes yerine string döndürür
            socket_timeout=5,          # Komut için maksimum bekleme süresi (saniye)
            socket_connect_timeout=2,  # Bağlantı kurulumu için maksimum bekleme süresi (saniye)
            retry_on_timeout=True,     # Zaman aşımı durumunda yeniden deneme
            max_connections=10,        # Maksimum bağlantı sayısı (bağlantı havuzu)
            socket_keepalive=True      # Bağlantıyı kalıcı tutar
        )

        # Redis istemcisi
        self.redis_client = redis.Redis(connection_pool=pool)