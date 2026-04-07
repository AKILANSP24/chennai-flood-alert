library(ggplot2)
library(dplyr)
library(lubridate)

# Ensure reports directory exists
dir.create("/data/reports", showWarnings = FALSE)

file_path <- "/data/alerts_log.csv"
if (!file.exists(file_path)) {
  writeLines("No alerts_log.csv found. Exiting.", stderr())
  quit(status = 0)
}

alerts <- read.csv(file_path,
  col.names = c("timestamp", "zone", "severity", "depth_cm", "report_count")
)

if (nrow(alerts) == 0) {
  writeLines("No alert data yet.", stderr())
  quit(status = 0)
}

alerts$timestamp <- ymd_hms(alerts$timestamp)
alerts$zone <- as.character(alerts$zone)
alerts$severity <- as.character(alerts$severity)

cat(paste("Processing", nrow(alerts), "alerts...\n"))

# Chart 1 — Alert timeline
p1 <- ggplot(alerts, aes(x = timestamp, y = depth_cm, color = severity)) +
  geom_point(size = 4) +
  geom_line(linewidth = 1) +
  scale_color_manual(values = c(
    "critical" = "#FF4444", "high" = "#FF8C00",
    "emergency" = "#CC0000", "medium" = "#FFA500"
  )) +
  labs(
    title = "Chennai Flood Alert Timeline",
    subtitle = paste("Total alerts:", nrow(alerts)),
    x = "Time", y = "Water Depth (cm)", color = "Severity"
  ) +
  theme_minimal(base_size = 14) +
  theme(plot.title = element_text(face = "bold", color = "#CC0000"))

ggsave("/data/reports/alert_timeline.png", p1, width = 12, height = 6, dpi = 150)
cat("Saved: alert_timeline.png\n")

# Chart 2 — Alerts by zone
zone_summary <- alerts %>%
  group_by(zone) %>%
  summarise(total_alerts = n(), max_depth = max(depth_cm, na.rm = TRUE)) %>%
  arrange(desc(total_alerts))

p2 <- ggplot(zone_summary, aes(
  x = reorder(zone, total_alerts),
  y = total_alerts, fill = max_depth
)) +
  geom_bar(stat = "identity") +
  coord_flip() +
  scale_fill_gradient(low = "#FFA500", high = "#FF0000") +
  labs(
    title = "Flood Alerts by Chennai Zone",
    subtitle = "Color intensity = maximum water depth",
    x = "Zone", y = "Number of Alerts", fill = "Max Depth (cm)"
  ) +
  theme_minimal(base_size = 14) +
  theme(plot.title = element_text(face = "bold"))

ggsave("/data/reports/zone_frequency.png", p2, width = 10, height = 6, dpi = 150)
cat("Saved: zone_frequency.png\n")

# Chart 3 — Severity breakdown
severity_counts <- alerts %>%
  group_by(severity) %>%
  summarise(count = n())

p3 <- ggplot(severity_counts, aes(x = "", y = count, fill = severity)) +
  geom_bar(stat = "identity", width = 1) +
  coord_polar("y") +
  scale_fill_manual(values = c(
    "critical" = "#FF4444", "high" = "#FF8C00",
    "emergency" = "#CC0000", "medium" = "#FFA500",
    "low" = "#90EE90"
  )) +
  labs(
    title = "Alert Severity Distribution",
    fill = "Severity"
  ) +
  theme_void(base_size = 14) +
  theme(plot.title = element_text(face = "bold", hjust = 0.5))

ggsave("/data/reports/severity_distribution.png", p3, width = 8, height = 6, dpi = 150)
cat("Saved: severity_distribution.png\n")

# Chart 4 — Depth distribution
p4 <- ggplot(alerts, aes(x = depth_cm, fill = severity)) +
  geom_histogram(bins = 15, alpha = 0.8, color = "white") +
  geom_vline(
    xintercept = 50, color = "red", linetype = "dashed",
    linewidth = 1.5
  ) +
  annotate("text",
    x = 52, y = Inf, label = "Alert threshold\n(50cm)",
    hjust = 0, vjust = 1.5, color = "red", size = 4
  ) +
  scale_fill_manual(values = c(
    "critical" = "#FF4444", "high" = "#FF8C00",
    "emergency" = "#CC0000", "medium" = "#FFA500"
  )) +
  labs(
    title = "Water Depth Distribution Across All Alerts",
    x = "Water Depth (cm)", y = "Count", fill = "Severity"
  ) +
  theme_minimal(base_size = 14)

ggsave("/data/reports/depth_distribution.png", p4, width = 10, height = 6, dpi = 150)
cat("Saved: depth_distribution.png\n")

# Summary report
cat("\n=== CHENNAI FLOOD ALERT SUMMARY ===\n")
cat(paste("Total alerts fired:", nrow(alerts), "\n"))
cat(paste("Zones affected:", length(unique(alerts$zone)), "\n"))
cat(paste("Max water depth:", max(alerts$depth_cm, na.rm = TRUE), "cm\n"))
cat(paste("Critical alerts:", sum(alerts$severity %in% c("critical", "emergency")), "\n"))
cat(paste(
  "Date range:", format(min(alerts$timestamp), "%Y-%m-%d"),
  "to", format(max(alerts$timestamp), "%Y-%m-%d"), "\n"
))
cat("Reports saved to /data/reports/\n")
