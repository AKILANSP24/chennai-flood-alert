@echo off
echo Starting Chennai Flood Alert System...
docker compose up -d
echo Waiting 30 seconds for Kafka...
timeout /t 30 /nobreak
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic citizen-raw --partitions 1 --replication-factor 1 2>nul
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic weather-raw --partitions 1 --replication-factor 1 2>nul
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic nlp-results --partitions 1 --replication-factor 1 2>nul
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic risk-scores --partitions 1 --replication-factor 1 2>nul
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic final-alerts --partitions 1 --replication-factor 1 2>nul
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic reservoir-raw --partitions 1 --replication-factor 1 2>nul
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic weather-aggregates --partitions 1 --replication-factor 1 2>nul
echo All topics ready.
docker compose restart decision-engine nlp-service telegram-bot
timeout /t 15 /nobreak
docker ps --format "{{.Names}}: {{.Status}}"
start http://localhost:8081
echo SYSTEM READY
pause