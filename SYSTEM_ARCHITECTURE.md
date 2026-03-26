# Chennai Flood Alert System: Architecture & Design Document

## Executive Summary
The Chennai Flood Alert System is an intelligent, event-driven platform designed to provide early warnings and actionable insights during heavy rainfall and flooding events. By combining real-time citizen crowdsourcing, meteorological data, and advanced Natural Language Processing (NLP), the platform continuously assesses risk and dispatches automated alerts to the public.

## Core Infrastructure
The system operates on a decentralized microservices model, maximizing resilience and throughput. All modules communicate entirely through a central message broker backbone. The platform utilizes an in-memory data grid for the rapid evaluation of ongoing events, and utilizes PySpark for heavy stream analytics.

---

## Operational Workflow

### Phase 1: Data Ingestion
The platform securely gathers information from three primary external sources:

| Component | Function | Data Output |
| :--- | :--- | :--- |
| **Telegram Interface** | Acts as the public portal for citizens to submit text, photos, and location pins regarding flood conditions. User privacy is maintained via secure hashing algorithms. | Crowdsourced incident reports. |
| **Meteorological Link** | Periodically connects to external cloud weather infrastructure to acquire hyper-local precipitation metrics (1-hour and 3-hour rainfall accumulations) and humidity data specifically for the Chennai region. | Verified weather telemetry. |
| **Reservoir Monitor** | Runs automated scheduled checks to aggregate current water levels and total storage capacity across primary Chennai reservoirs (such as Chembarambakkam, Puzhal, and Poondi). | Water level metrics. |

### Phase 2: Intelligence & Stream Processing
Once raw data is ingested, the system rigorously cleans, categorizes, and analyzes it.

1. **Geospatial Processing**
   - All incoming localized data is mapped to an exact geospatial grid to allow for high-accuracy neighborhood tracking.
   - Weather telemetry is aggregated over a rolling observation window to establish continuous physical threat metrics.
   - Citizen reports are immediately forwarded to the internal NLP engine for deep linguistic analysis.

2. **Linguistic Analysis (NLP Pipeline)**
   - **Normalization**: Regional slang ("Tanglish") is translated and normalized against a predefined local dictionary.
   - **Noise Filtering**: A lightweight classification AI scans the text to discard casual conversation or spam, ensuring only genuine emergency reports proceed through the pipeline.
   - **Deep Extraction**: A locally hosted predictive AI engine structurally reads the emergency report, interpreting the exact severity of the situation, extracting the estimated water depth, and interpreting complex location descriptions.

### Phase 3: Decision Engine Logic
The core "brain" of the platform is the Decision Engine. It continuously evaluates the intelligent data streams to determine if a public alert is necessary. It relies on a time-sensitive sliding window (tracking the density of reports in a specific neighborhood over a 10-minute span).

**Alert Triggers:**
- **Red Alert (Critical Threat)**: Triggered immediately if the extracted water depth exceeds 50 centimeters, or if there is a massive cluster of high-severity emergency reports from the exact same neighborhood within a 10-minute period.
- **Orange Alert (High Threat)**: Triggered as a cautionary warning when severe conditions begin forming but haven't yet eclipsed critical mass.

When triggered, the Decision Engine permanently archives the event and dispatches an alert command back to the Telegram Interface for public broadcasting.

### Phase 4: Visualization & Reporting
The platform maintains a permanent visual record of events for historical analysis and review.
- **Analytics Engine**: Powered by R, this utility routinely reads the archived alert history.
- **Outputs**: It automatically generates timeline graphs contrasting rainfall against flood depth, categorizes the most heavily affected zones, and renders an interactive web map plotting the exact radius and severity of historic flood alerts.
