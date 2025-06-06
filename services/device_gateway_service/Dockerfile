FROM python:3.12.7-slim

WORKDIR /app

ARG RABBITMQ_HOST
ARG RABBITMQ_USER
ARG RABBITMQ_PASSWORD
ARG EXCHANGE_NAME
ARG EXCHANGE_FANOUT
ARG QUEUE_KPI
ARG QUEUE_FRONTEND
ARG ELASTICSEARCH_HOST
ARG ELASTICSEARCH_CONNECTION
ARG ELASTICSEARCH_PORT
ARG DATABASE_HOST
ARG DATABASE_NAME
ARG DATABASE_USERNAME
ARG DATABASE_PASSWORD
ARG API_KEY

ENV RABBITMQ_HOST=${RABBITMQ_HOST}
ENV RABBITMQ_USER=${RABBITMQ_USER}
ENV RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD}
ENV EXCHANGE_NAME=${EXCHANGE_NAME}
ENV EXCHANGE_FANOUT=${EXCHANGE_FANOUT}
ENV QUEUE_KPI=${QUEUE_KPI}
ENV QUEUE_FRONTEND=${QUEUE_FRONTEND}
ENV ELASTICSEARCH_HOST=${ELASTICSEARCH_HOST}
ENV ELASTICSEARCH_CONNECTION=${ELASTICSEARCH_CONNECTION}
ENV ELASTICSEARCH_PORT=${ELASTICSEARCH_PORT}
ENV DATABASE_HOST=${DATABASE_HOST}
ENV DATABASE_NAME=${DATABASE_NAME}
ENV DATABASE_USERNAME=${DATABASE_USERNAME}
ENV DATABASE_PASSWORD=${DATABASE_PASSWORD}
ENV API_KEY=${API_KEY}

COPY services /app/services
COPY shared /app/shared
COPY services/device_gateway_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

CMD ["python", "-m", "services.device_gateway_service.main"]