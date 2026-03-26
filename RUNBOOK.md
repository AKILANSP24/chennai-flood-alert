# Chennai Flood Alert System: Operator's Manual

## Overview
This document provides the standard operating procedures for managing the Chennai Flood Alert System. It is designed for system administrators, operators, and incident managers responsible for safely launching, monitoring, and shutting down the platform.

## 1. System Requirements
Before initiating the system, ensure the host environment meets the following criteria:
- **Containerization Platform**: Docker Engine and Docker Compose must be installed and actively running.
- **Authentication Credentials**: A configured environment file (often named `.env`) must be present in the primary directory, containing secure access keys (such as the Telegram Bot Token and OpenWeatherMap API Key).

## 2. Operational Procedures

### Initiating the Platform
To launch the entire suite of services, use the standard container initialization command from the project root directory:

`docker compose up -d`

*Note: The system will automatically orchestrate the startup sequence for all internal message brokers, databases, processing engines, and scrapers in the background.*

### Halting Operations
To safely suspend all active operations and gracefully shut down the platform:

`docker compose down`

*Note: This command preserves all retained data. If a complete factory reset is required (which will erase all historical data and temporary models), the volume teardown flag (`-v`) can be appended to the command.*

## 3. System Monitoring
Operators can monitor the real-time health and activity of the system via the command line interface:

- **Global View**: To view a live stream of all system activities simultaneously, execute `docker compose logs -f`.
- **Specific Component Focus**: To isolate the activity of a single service (for example, the Natural Language Processing engine), designate the component name: `docker compose logs -f nlp-service`.

## 4. Expected System Behavior
Once the platform successfully initializes, operators will observe the following active states:
- **Data Ingestion**: The weather monitoring modules will confirm successful connections to external weather APIs.
- **Communication Pipelines**: The Telegram Bot will actively report that it is listening and ready to process incoming citizen reports.
- **Analytics Generation**: The R-Analysis module will periodically activate in the background to generate fresh visual reports and maps based on the latest alert data, before returning to a dormant state.
- **User Interface**: The system's primary dashboard will become accessible via web browser at standard local connection ports (typically `http://localhost:8081`).
