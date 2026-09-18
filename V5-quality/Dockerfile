FROM python:3.12-slim

WORKDIR /app

# Pas d'apt : psycopg2-binary et pandas sont precompiles (wheels),
# prometheus-client est pur Python. Build en 1-2 min.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
