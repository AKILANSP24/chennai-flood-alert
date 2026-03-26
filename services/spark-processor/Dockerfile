FROM bitnami/spark:3.5
USER root
RUN pip install --no-cache-dir -r requirements.txt
USER 1001
WORKDIR /app
COPY . .
# CMD ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.sedona:sedona-spark-shaded-3.0_2.12:1.5.0", "main.py"]
