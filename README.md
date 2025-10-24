# Weather Forecast Docker Application

This Docker application fetches local and marine weather forecasts for Alaska's Pribilof Islands - St. Paul Island (99660) and St. George Island (99591) - using the NOAA/NWS API.

## Features

- **Local Forecasts**: 7-day weather forecasts for both Pribilof Islands
- **Marine Forecasts**: Marine weather for Pribilof Islands Nearshore Waters (PKZ766)
- **Automatic Updates**: Configurable update interval (default: 1 hour)
- **Data Persistence**: Saves forecasts in both JSON and text formats
- **Separate Files**: Individual files for each island and marine forecasts
- **Free API**: Uses NOAA's free National Weather Service API and text products

## Configuration

Environment variables (set in docker-compose.yml):

- `ZIP_CODES`: Comma-separated list of zip codes (default: "99660,99591")
- `UPDATE_INTERVAL`: Update interval in seconds (default: 3600 = 1 hour)
- `TZ`: Timezone (set to: America/Anchorage)

## Output Files

The application saves forecast data to the `/data` volume:

### Combined Forecasts
- `/data/latest_forecast.json`: All forecast data in JSON format
- `/data/latest_forecast.txt`: All forecasts in human-readable format

### Individual Island Forecasts
- `/data/st._paul_island_99660.json`: St. Paul Island data (JSON)
- `/data/st._paul_island_99660.txt`: St. Paul Island forecast (text)
- `/data/st._george_island_99591.json`: St. George Island data (JSON)
- `/data/st._george_island_99591.txt`: St. George Island forecast (text)

### Marine Forecasts
- `/data/pribilof_island_waters.json`: Marine forecast data (JSON)
- `/data/pribilof_island_waters.txt`: Marine forecast (text)

## Marine Zone Covered

- **PKZ766**: Pribilof Islands Nearshore Waters (Bering Sea)

## Usage

### Start the service:
```bash
docker-compose up -d weather-forecast
```

### View logs:
```bash
docker-compose logs -f weather-forecast
```

### View forecasts:

**View all forecasts (combined):**
```bash
cat /opt/dockers/weather-forecast/data/latest_forecast.txt
```

**View St. Paul Island forecast:**
```bash
cat /opt/dockers/weather-forecast/data/st._paul_island_99660.txt
```

**View St. George Island forecast:**
```bash
cat /opt/dockers/weather-forecast/data/st._george_island_99591.txt
```

**View marine forecast (Pribilof Islands Nearshore Waters):**
```bash
cat /opt/dockers/weather-forecast/data/pribilof_island_waters.txt
```

### Stop the service:
```bash
docker-compose down weather-forecast
```

## Data Sources

This application uses multiple NOAA data sources:

- **Local Forecasts**: NOAA National Weather Service API
  - API: https://api.weather.gov
  - No API key required
  - Documentation: https://www.weather.gov/documentation/services-web-api

- **Marine Forecasts**: NOAA Text Products
  - Source: https://tgftp.nws.noaa.gov/data/raw/fz/fzak52.pafc.cwf.alu.txt
  - Updates: Multiple times daily
  - Includes Small Craft Advisories and marine conditions

## Locations

- **St. Paul Island (99660)**: 57.1253°N, 170.2806°W
- **St. George Island (99591)**: 56.5983°N, 169.5464°W
- **Marine Zone PKZ766**: Pribilof Islands Nearshore Waters (Bering Sea)
