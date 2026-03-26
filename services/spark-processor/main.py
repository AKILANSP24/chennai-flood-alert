import os
import h3
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, window, sum as _sum, udf, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType
from sedona.spark import SedonaContext

# Kafka configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")

# Schemas
weather_schema = StructType([
    StructField("source", StringType(), True),
    StructField("lat", DoubleType(), True),
    StructField("lon", DoubleType(), True),
    StructField("temp_c", DoubleType(), True),
    StructField("humidity", DoubleType(), True),
    StructField("rain_1h_mm", DoubleType(), True),
    StructField("rain_3h_mm", DoubleType(), True),
    StructField("timestamp", LongType(), True)
])

citizen_schema = StructType([
    StructField("user_id_hash", StringType(), True),
    StructField("lat", DoubleType(), True),
    StructField("lon", DoubleType(), True),
    StructField("text", StringType(), True),
    StructField("ts", StringType(), True)
])

# UDF mapping coordinates to H3 hex resolution 9 (approx 174m edge)
@udf(returnType=StringType())
def lat_lon_to_h3(lat, lon):
    if lat is None or lon is None:
        return None
    return h3.latlng_to_cell(lat, lon, 9)

def process_streams():
    # Initialize Spark with Sedona extensions
    config = {
        "spark.jars.packages": "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.sedona:sedona-spark-shaded-3.0_2.12:1.5.0",
        "spark.sql.extensions": "org.apache.sedona.sql.SedonaSqlExtensions",
        "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
        "spark.kryo.registrator": "org.apache.sedona.core.serde.SedonaKryoRegistrator"
    }

    builder = SparkSession.builder.appName("ChennaiFloodAlertProcessor")
    for k, v in config.items():
        builder = builder.config(k, v)
    
    spark = builder.getOrCreate()
    # Apply Sedona context (Used later to read shapefiles into SRDDs)
    spark = SedonaContext.create(spark)
    
    print("Starting PySpark Structured Streaming with Sedona Integration...")

    # 1. Weather Stream (2-hour rolling window)
    weather_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", "weather-raw") \
        .option("startingOffsets", "latest") \
        .load()
    
    weather_parsed = weather_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), weather_schema).alias("data")).select("data.*") \
        .withColumn("timestamp_ts", current_timestamp()) \
        .withColumn("h3_index", lat_lon_to_h3(col("lat"), col("lon")))

    weather_windowed = weather_parsed \
        .withWatermark("timestamp_ts", "10 minutes") \
        .groupBy(window(col("timestamp_ts"), "2 hours", "1 hour"), col("h3_index")) \
        .agg(_sum("rain_1h_mm").alias("total_rain_mm"))

    # Write aggregated metrics to another Kafka topic to feed the Decision Engine
    weather_query = weather_windowed.selectExpr("to_json(struct(*)) AS value") \
        .writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("topic", "risk-scores") \
        .option("checkpointLocation", "/tmp/spark/checkpoints/weather") \
        .start()

    # 2. Citizen Message Forwarding Stream
    # We forward raw citizen text directly into the NLP pipeline for categorization
    citizen_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", "citizen-raw") \
        .option("startingOffsets", "latest") \
        .load()

    citizen_parsed = citizen_df.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), citizen_schema).alias("data")).select("data.*") \
        .withColumn("h3_index", lat_lon_to_h3(col("lat"), col("lon")))
        
    citizen_query = citizen_parsed.selectExpr("to_json(struct(*)) AS value") \
        .writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("topic", "nlp-results") \
        .option("checkpointLocation", "/tmp/spark/checkpoints/citizen") \
        .start()

    # Block thread and await streaming processing
    spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    process_streams()
