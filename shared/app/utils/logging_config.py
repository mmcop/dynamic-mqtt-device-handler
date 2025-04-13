import logging
import logging.config
from elasticsearch import Elasticsearch
import json
import time

class ElasticsearchHandler(logging.Handler):
    def __init__(self, hosts=None, index_name='python-logs', max_retries=3, retry_delay=5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hosts = hosts
        self.index_name = index_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.es_client = self._connect_to_elasticsearch()

    def _connect_to_elasticsearch(self):
        retries = 0
        while retries < self.max_retries:
            try:
                es_client = Elasticsearch(hosts=self.hosts)
                if es_client.ping():
                    logging.info("Connected to Elasticsearch")
                    return es_client
                else:
                    raise logging.error("Elasticsearch ping failed.")
            except Exception as e:
                retries += 1
                logging.error(f"Elasticsearch connection failed: {e}. Retrying {retries}/{self.max_retries}...")
                time.sleep(self.retry_delay)
        raise logging.error("Failed to connect to Elasticsearch after multiple attempts.")

    def emit(self, record):
        if not self.es_client:
            logging.error("Elasticsearch client not available.")
            return

        try:
            log_entry = self.format(record)
            # Logu Elasticsearch'e gönderme
            self.es_client.index(index=self.index_name, body=json.loads(log_entry))
        except Exception as e:
            logging.error(f"Failed to send log to Elasticsearch: {e}")

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_message = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
            "module": record.module,
            "filename": record.filename,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        return json.dumps(log_message)

logging.getLogger('elastic_transport').setLevel(logging.WARNING)
logging.getLogger('pika').setLevel(logging.CRITICAL)


def get_logging_config(service_name, es_host=None, es_start=False, index_name= 'python-logs'):
    log_level = {
        'user_device_connection_permission_service': 'INFO',
        'device_gateway_service': 'INFO',
        'device_message_handler_service': 'INFO'
    }

    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': f'%(asctime)s - {service_name} - %(levelname)s - %(module)s - %(filename)s - %(lineno)d - %(message)s'
            },
            'json': {
                '()': JSONFormatter,
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'standard',
            },
            #'file': {
            #    'class': 'logging.FileHandler',
            #    'level': 'INFO',
            #    'formatter': 'standard',
            #    'filename': f'{service_name}.log',
            #},
        },
        'loggers': {
            service_name: {
                'handlers': ['console'],
                'level': log_level.get(service_name, 'INFO'),
                'propagate': False
            }
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }

    if es_start and es_host:
        config['handlers']['elasticsearch'] = {
            'class': 'shared.app.utils.logging_config.ElasticsearchHandler',
            'level': 'ERROR',
            'formatter': 'json',
            'hosts': es_host,
            'index_name': index_name,
        }
        config['loggers'][service_name]['handlers'].append('elasticsearch')

    return config

def setup_logging(service_name, es_host=None, es_start=False, index_name='python-logs'):
    logging_config = get_logging_config(service_name, es_host, es_start, index_name)
    logging.config.dictConfig(logging_config)
    return logging.getLogger(service_name)
