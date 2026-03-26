if (!requireNamespace("leaflet", quietly=TRUE))
  install.packages("leaflet", repos="https://cran.r-project.org")
if (!requireNamespace("htmlwidgets", quietly=TRUE))
  install.packages("htmlwidgets", repos="https://cran.r-project.org")

library(ggplot2)
library(leaflet)
library(rmarkdown)
library(dplyr)
library(lubridate)

# Ensure reports directory exists
dir.create("/data/reports", showWarnings = FALSE)

# Read alert log written by decision engine
file_path <- "/data/alerts_log.csv"
if(!file.exists(file_path)) {
  writeLines("No alerts_log.csv found. Exiting.", stderr())
  quit(status=0)
}

alerts <- read.csv(file_path,
  col.names = c("timestamp","zone","severity","depth_cm","report_count"))

alerts$timestamp <- ymd_hms(alerts$timestamp)

# Chart 1 — alert frequency over time
if (nrow(alerts) >= 2) {
  ggplot(alerts, aes(x = timestamp, y = depth_cm, color = severity)) +
    geom_line() + geom_point(size = 3) +
    geom_point(size = 3, shape = 21, fill = "white") +
    labs(title = "Chennai Flood Alert Timeline",
         x = "Time", y = "Water Depth (cm)") +
    theme_minimal()

  ggsave("/data/reports/alert_timeline.png")
} else {
  message("Not enough data for timeline chart yet.")
}

# Chart 2 — which zones triggered most alerts
ggplot(alerts, aes(x = reorder(zone, report_count), y = report_count, fill = severity)) +
  geom_bar(stat = "identity") +
  coord_flip() +
  labs(title = "Alert Frequency by Zone", x = "Zone", y = "Reports") +
  theme_minimal()

ggsave("/data/reports/zone_frequency.png")

# Chart 3 — interactive map using leaflet
zone_coords <- data.frame(
  zone = c("Velachery","Tambaram","Saidapet","Adyar","Mudichur",
           "T Nagar","Anna Nagar","Porur","Chrompet","Perambur"),
  lat  = c(12.9815, 12.9249, 13.0201, 13.0067, 12.9100,
           13.0418, 13.0850, 13.0359, 12.9516, 13.1167),
  lon  = c(80.2180, 80.1000, 80.2201, 80.2510, 80.0700,
           80.2341, 80.2101, 80.1560, 80.1462, 80.2334)
)

map_data <- alerts %>%
  group_by(zone) %>%
  summarise(total_alerts = n(), max_depth = max(depth_cm, na.rm=TRUE)) %>%
  left_join(zone_coords, by = "zone") %>%
  filter(!is.na(lat) & !is.na(lon))

# Leaflet output as html
map <- leaflet(map_data) %>%
  addTiles() %>%
  addCircleMarkers(
    ~lon, ~lat,
    radius     = ~total_alerts * 5,
    color      = ~ifelse(max_depth > 50, "red", "orange"),
    label      = ~paste(zone, "—", total_alerts, "alerts, max depth:", max_depth, "cm"),
    fillOpacity = 0.7
  ) %>%
  addLegend("bottomright",
    colors = c("red","orange"),
    labels = c("Critical (>50cm)","High"),
    title  = "Alert Level"
  )

# Save the map html
library(htmlwidgets)
saveWidget(map, file="/data/reports/interactive_flood_map.html")
