# IoT Cihaz Yönetim Platformu

Kapsamlı, mikroservis tabanlı bir IoT cihaz yönetim platformu. Cihaz bağlantılarını, mesaj işlemeyi, kullanıcı yönetimini ve alarm izlemeyi IoT ekosistemleri için entegre bir şekilde yönetir.

## Mimari Genel Bakış

Platform dört ana mikroservisten oluşmaktadır:

1. **User Device Connection Permission Service** - Kullanıcı oluşturma ve izinlerini yönetir
2. **Device Gateway Service** - MQTT bağlantılarını ve konu aboneliklerini işler
3. **Device Message Handler Service** - Cihaz mesajlarını işler ve depolar
4. **Device Alarm Service** - Cihaz verilerini izler ve kurallara göre alarmlar tetikler

## Servisler

### User Device Connection Permission Service

Bu servis, cihaz bağlantıları için kullanıcı erişim kontrolünü ve izinlerini yönetir.

**Yetenekler:**
- Belirli erişim haklarına sahip kullanıcılar oluşturma, güncelleme ve silme
- Kullanıcılar için RabbitMQ izinlerini ayarlama
- MQTT bağlantıları için topic düzeyinde izinleri yapılandırma
- Kullanıcı durumunu veritabanında takip etme
- RabbitMQ REST API ile entegrasyon sayesinde yetkilendirme işlemlerini otomatize etme
- Asenkron işlem takibi için çoklu iş parçacığı desteği
- API anahtarı tabanlı güvenlik katmanı

**API Uç Noktaları:**
- `POST /user/create` - Yeni bir kullanıcı oluştur
- `PUT /user/update` - Mevcut bir kullanıcıyı güncelle
- `PUT /user/delete` - Bir kullanıcıyı sil

### Device Gateway Service

Bu servis, farklı türlerdeki istemciler için MQTT bağlantılarını ve topic aboneliklerini yönetir.

**Yetenekler:**
- Ücretsiz, temel ve premium abonelik seviyeleri için özelleştirilmiş bağlantı yönetimi
- Abonelik seviyesine göre hız sınırlaması uygulama
- Cihaz doğrulaması için test bağlantıları desteği
- İşleme için cihaz mesajlarını RabbitMQ'ya iletme
- Bağlantı durumunu thread-safe bir şekilde izleme
- Dinamik topic dinleme ve ayrılma imkanı
- Çoklu kiracı (multi-tenant) desteği ile farklı şirketlere ait cihazların izole edilmesi
- Cihaz bağlantılarını abonelik seviyelerine göre havuzlama
- Bağlantı havuzlarını verimli yönetmek için akıllı kaynak tahsisi
- API anahtarı tabanlı güvenlik katmanı

**API Uç Noktaları:**
- `POST /gateway/topic-listen` - Bir topic'e abone ol
- `POST /gateway/test-topic-listen` - Bir topic bağlantısını test et
- `PUT /gateway/topic-remove` - Bir topic'ten aboneliği kaldır
- `PUT /gateway/topic-listen-close` - Bir topic aboneliğini kapat

### Device Message Handler Service

Bu servis, cihaz mesajlarını işler ve veritabanında saklar.

**Yetenekler:**
- RabbitMQ kuyruklarından mesajları tüketme
- Mesajları PostgreSQL veritabanında işleme ve saklama
- Dead letter exchange ile mesaj yeniden deneme mekanizması
- İşleme hatalarını raporlama
- Yüksek hacimli mesaj işleme için optimize edilmiş mimari
- Mesaj işleme hatalarında akıllı yeniden deneme stratejisi
- Thread havuzları ile paralel mesaj işleme
- Elasticsearch entegrasyonu ile gelişmiş log takibi

### Device Alarm Service

Bu servis, cihaz verilerini izler ve yapılandırılabilir kurallara göre alarmlar tetikler.

**Yetenekler:**
- Karmaşık mantık ile alarm kuralları tanımlama ve değerlendirme
- Çeşitli karşılaştırma operatörlerini destekleme (>, <, ==, >=, <=, !=)
- Karmaşık koşullar için logical operatörleri kullanma (AND, OR, NOT)
- Daha iyi performans için Redis önbelleğinde alarm tanımlarını saklama
- Alarm koşulları karşılandığında bildirimler gönderme
- Hiyerarşik kural grupları ile esnek alarm yapılandırması
- Alarm işleme optimizasyonu için önbellekleme stratejisi
- RabbitMQ entegrasyonu ile veri akışını dinleme

## Ortak Modüller (shared/app)

Platform, tüm servislerin kullandığı ortak bileşenlerden yararlanır:

### RabbitMQ Modülleri

**Yetenekler:**
- `RabbitMQProducer`: Temel mesaj gönderme işlevselliği
- `RabbitMQProducerFanout`: Yayın modeli mesaj dağıtımı
- `RabbitMQConsumer`: Hata işleme ve yeniden deneme mekanizmalı mesaj tüketimi
- `RabbitMQConsumerAlarm`: Alarm servisi için özelleştirilmiş tüketici
- Otomatik bağlantı yeniden kurma ve hata yönetimi
- Asenkron mesaj işleme ve ölçeklenebilir tüketici modeli

### PostgreSQL Modülleri

**Yetenekler:**
- `PostgreSQLClient`: Temel veritabanı işlemleri
- `PostgreSQLORMClient`: ORM tabanlı veritabanı işlemleri
- `PostgreSQLORMClientSingle`: Singleton tasarım modeliyle kaynak optimizasyonu
- Bağlantı havuzu yönetimi ve sağlık kontrolü
- Dinamik sorgu oluşturma ve veri manipülasyonu
- Veritabanı şema yönetimi

## Önkoşullar

- Docker ve Docker Compose
- PostgreSQL veritabanı
- Redis önbelleği
- MQTT eklentili RabbitMQ sunucusu
- Elasticsearch (isteğe bağlı, loglama için)

## Yapılandırma

Her servis, yapılandırma için ortam değişkenleri gerektirir. Temel değişkenler şunları içerir:

```
# Veritabanı Yapılandırması
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=iotplatform
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=yourpassword

# RabbitMQ Yapılandırması
RABBITMQ_HOST=rabbitmq
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
AMQP_PORT=5672
MQTT_PORT=1883

# Servis-özel Yapılandırma
API_KEY=your-api-key
ELASTICSEARCH_CONNECTION=True
ELASTICSEARCH_HOST=elasticsearch
ELASTICSEARCH_PORT=9200
```

## AWS Entegrasyonu ve Dağıtım

Platform, AWS ortamında dağıtım için hazır durumdadır:

### BuildSpec Dosyaları

Her hizmet, AWS CodeBuild ile entegrasyon için buildspec.yml dosyaları içerir. Bu dosyalar:

- AWS ECR'ye otomatik Docker imajı dağıtımını yapılandırır
- CI/CD iş akışını otomatikleştirir
- Güvenli şekilde hassas yapılandırmaları yönetir

BuildSpec örneği:
```yaml
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_DEFAULT_ACCOUNT.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com

  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -f services/device_gateway_service/$DOCKERFILE --build-arg RABBITMQ_HOST=$RABBITMQ_HOST --build-arg RABBITMQ_USER=$RABBITMQ_USER --build-arg RABBITMQ_PASSWORD=$RABBITMQ_PASSWORD [diğer parametreler]...

  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker image to ECR...
      - docker push $AWS_DEFAULT_ACCOUNT.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
```

### Dockerfile Güvenliği

Tüm servisler için Dockerfile'lar, ortam değişkenlerini build-arg olarak alır, bu da hassas bilgilerin güvenli bir şekilde yönetilmesini sağlar:

```Dockerfile
FROM python:3.12.7-slim

WORKDIR /app

ARG RABBITMQ_HOST
ARG RABBITMQ_USER
ARG RABBITMQ_PASSWORD
# Diğer argümanlar...

ENV RABBITMQ_HOST=${RABBITMQ_HOST}
ENV RABBITMQ_USER=${RABBITMQ_USER}
ENV RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD}
# Diğer çevre değişkenleri...

COPY services /app/services
COPY shared /app/shared
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

CMD ["python", "-m", "services.service_name.main"]
```

## Servisleri Çalıştırma

### Docker Kullanarak

Her servis, konteynerleştirme için bir Dockerfile içerir. Servisleri tek tek oluşturup çalıştırabilirsiniz:

#### User Device Connection Permission Service

```bash
# Image oluşturma
docker build -t user_device_connection_permission_service -f ./services/user_device_connection_permission_service/Dockerfile .

# Container çalıştırma
docker run -d --name user_device_connection_permission_service \
  -e DEVICE_MQTT_SERVICE_URL=http://gateway-service-url:5001 \
  -e API_KEY=your_api_key \
  -e DATABASE_HOST=your_db_host \
  -e DATABASE_NAME=your_db_name \
  -e DATABASE_PASSWORD=your_password \
  -e DATABASE_USERNAME=your_username \
  -e ELASTICSEARCH_CONNECTION=False \
  -e ELASTICSEARCH_HOST=your_es_host \
  -e ELASTICSEARCH_PORT=9200 \
  -e RABBITMQ_HOST=http://your_rabbitmq_host:15672 \
  -e RABBITMQ_PASSWORD=your_rabbitmq_password \
  -e RABBITMQ_USER=your_rabbitmq_user \
  -p 5000:5000 user_device_connection_permission_service
```

#### Device Gateway Service

```bash
# Image oluşturma
docker build -t device_gateway_service -f ./services/device_gateway_service/Dockerfile .

# Container çalıştırma
docker run -d --name device_gateway_service \
  -e API_KEY=your_api_key \
  -e DATABASE_HOST=your_db_host \
  -e DATABASE_NAME=your_db_name \
  -e DATABASE_PASSWORD=your_password \
  -e DATABASE_USERNAME=your_username \
  -e ELASTICSEARCH_CONNECTION=False \
  -e ELASTICSEARCH_HOST=your_es_host \
  -e ELASTICSEARCH_PORT=9200 \
  -e EXCHANGE_NAME=mm_message_flow_exchange \
  -e EXCHANGE_FANOUT=mm_device_data_exchange \
  -e QUEUE_FRONTEND=mm_device_data_queue \
  -e QUEUE_KPI=mm_device_data_kpi_queue \
  -e RABBITMQ_HOST=your_rabbitmq_host \
  -e RABBITMQ_PASSWORD=your_rabbitmq_password \
  -e RABBITMQ_USER=your_rabbitmq_user \
  -p 5001:5001 device_gateway_service
```

#### Device Message Handler Service

```bash
# Image oluşturma
docker build -t device_message_handler_service -f ./services/device_message_handler_service/Dockerfile .

# Container çalıştırma
docker run -d --name device_message_handler_service \
  -e API_KEY=your_api_key \
  -e DATABASE_HOST=your_db_host \
  -e DATABASE_NAME=your_db_name \
  -e DATABASE_PASSWORD=your_password \
  -e DATABASE_USERNAME=your_username \
  -e ELASTICSEARCH_CONNECTION=False \
  -e ELASTICSEARCH_HOST=your_es_host \
  -e ELASTICSEARCH_PORT=9200 \
  -e EXCHANGE_NAME=mm_message_flow_exchange \
  -e DEAD_LETTER_EXCHANGE_NAME=dlx_exchange \
  -e DEAD_LETTER_QUEUE_NAME=dlx_queue \
  -e QUEUE_NAME=mm_device_data_gateway_queue \
  -e RABBITMQ_HOST=your_rabbitmq_host \
  -e RABBITMQ_PASSWORD=your_rabbitmq_password \
  -e RABBITMQ_USER=your_rabbitmq_user \
  device_message_handler_service
```

#### Device Alarm Service

```bash
# Image oluşturma
docker build -t device_alarm_service -f ./services/device_alarm_service/Dockerfile .

# Container çalıştırma
docker run -d --name device_alarm_service \
  -e API_KEY=your_api_key \
  -e DATABASE_HOST=your_db_host \
  -e DATABASE_NAME=your_db_name \
  -e DATABASE_PASSWORD=your_password \
  -e DATABASE_USERNAME=your_username \
  -e ELASTICSEARCH_CONNECTION=False \
  -e ELASTICSEARCH_HOST=your_es_host \
  -e ELASTICSEARCH_PORT=9200 \
  -e QUEUE_NAME=mm_device_data_alarm_queue \
  -e RABBITMQ_HOST=your_rabbitmq_host \
  -e RABBITMQ_PASSWORD=your_rabbitmq_password \
  -e RABBITMQ_USER=your_rabbitmq_user \
  device_alarm_service
```

Alternatif olarak, Docker Compose ile tüm servisleri birlikte oluşturup çalıştırabilirsiniz:

```bash
docker-compose up --build
```

### Manuel Kurulum

1. Depoyu klonlayın
2. Her servis için bağımlılıkları yükleyin:
   ```bash
   pip install -r services/device_gateway_service/requirements.txt
   pip install -r services/device_message_handler_service/requirements.txt
   pip install -r services/device_alarm_service/requirements.txt
   pip install -r services/user_device_connection_permission_service/requirements.txt
   ```
3. Gerektiği gibi ortam değişkenlerini yapılandırın
4. Her servisi başlatın:
   ```bash
   python -m services.device_gateway_service.main
   python -m services.device_message_handler_service.main
   python -m services.device_alarm_service.main
   python -m services.user_device_connection_permission_service.main
   ```

## Veritabanı Şeması

Platform, aşağıdaki temel tablolarla PostgreSQL kullanır:

- `mm_device.device_data` - Cihaz mesajlarını depolar
- `mm_device.device_test_connection_data` - Test bağlantı verilerini depolar
- `mm_device.task_states` - Servis işlemlerini izler
- `mm_device.alarm_definitions` - Alarm kurallarını tanımlar
- `mm_device.logic_groups` - Alarm kuralları için mantıksal gruplandırmaları tanımlar
- `mm_device.alarm_rules` - Alarmlar için belirli eşik kurallarını tanımlar

## Abonelik Seviyeleri

Platform üç abonelik seviyesini destekler:

- **Free** - Sınırlı mesaj hızı ve boyutu, veritabanı kalıcılığı yok
- **Basic** - Orta düzey mesaj hızı ve boyutu, veritabanı kalıcılığı ile
- **Premium** - En yüksek mesaj hızı ve boyutu, özel bağlantılar, tam veritabanı kalıcılığı

## İzleme ve Loglama

Platform, merkezi loglama için Elasticsearch entegrasyonu ile kapsamlı loglama içerir. Özellikler:

- Yapılandırılabilir log seviyeleri
- JSON formatında log yapılandırması
- Elasticsearch'e otomatik log gönderimi
- Servis bazlı log ayrıştırma
- Hata durumunda yeniden bağlanma mekanizması
