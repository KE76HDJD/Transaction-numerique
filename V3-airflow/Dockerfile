FROM python:3.11-slim

ENV AIRFLOW_HOME=/opt/airflow
ENV AIRFLOW__CORE__EXECUTOR=LocalExecutor
ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres-airflow:5432/airflow
ENV AIRFLOW__CORE__LOAD_EXAMPLES=false
ENV AIRFLOW__WEBSERVER__EXPOSE_CONFIG=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    "apache-airflow==2.10.5" \
    "psycopg2-binary>=2.9.0" \
    "pandas>=2.0.0" \
    "python-dotenv>=1.0.0"

RUN mkdir -p ${AIRFLOW_HOME}/dags ${AIRFLOW_HOME}/logs ${AIRFLOW_HOME}/plugins

COPY V3-airflow/dags ${AIRFLOW_HOME}/dags

WORKDIR ${AIRFLOW_HOME}

EXPOSE 8080

CMD ["airflow", "webserver"]
