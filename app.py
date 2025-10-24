#!/usr/bin/env python3
"""
Weather Forecast Application
Fetches local and marine forecasts for specified zip codes using NOAA/NWS API
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeatherForecastFetcher:
    """Fetches weather forecasts from NOAA/NWS API"""
    
    BASE_URL = "https://api.weather.gov"
    USER_AGENT = "WeatherForecastApp/1.0"
    
    def __init__(self, zip_codes: List[str]):
        self.zip_codes = zip_codes
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
            'Accept': 'application/json'
        })
    
    def get_coordinates_from_zip(self, zip_code: str) -> Optional[Dict]:
        """Get latitude and longitude from zip code using geocoding API"""
        try:
            # Using a simple geocoding approach via NWS
            # For Alaska zip codes, we'll use known coordinates
            alaska_zips = {
                '99660': {'lat': 57.1253, 'lon': -170.2806, 'city': 'St. Paul Island'},
                '99591': {'lat': 56.5983, 'lon': -169.5464, 'city': 'St. George Island'}
            }
            
            if zip_code in alaska_zips:
                return alaska_zips[zip_code]
            
            logger.warning(f"Zip code {zip_code} not in predefined list")
            return None
            
        except Exception as e:
            logger.error(f"Error getting coordinates for {zip_code}: {e}")
            return None
    
    def get_forecast_urls(self, lat: float, lon: float) -> Optional[Dict]:
        """Get forecast URLs from NWS points endpoint"""
        try:
            url = f"{self.BASE_URL}/points/{lat},{lon}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'forecast': data['properties'].get('forecast'),
                'forecast_hourly': data['properties'].get('forecastHourly'),
                'forecast_grid_data': data['properties'].get('forecastGridData'),
                'observation_stations': data['properties'].get('observationStations'),
                'county': data['properties'].get('county'),
                'fire_weather_zone': data['properties'].get('fireWeatherZone')
            }
        except Exception as e:
            logger.error(f"Error getting forecast URLs for {lat},{lon}: {e}")
            return None
    
    def get_forecast(self, forecast_url: str) -> Optional[Dict]:
        """Get the actual forecast data"""
        try:
            response = self.session.get(forecast_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data['properties']
        except Exception as e:
            logger.error(f"Error getting forecast from {forecast_url}: {e}")
            return None
    
    def get_marine_forecast(self, lat: float, lon: float) -> Optional[Dict]:
        """Get marine forecast for coastal areas"""
        try:
            marine_data = {}
            
            # Fetch PKZ766 from NOAA text product
            try:
                text_url = "https://tgftp.nws.noaa.gov/data/raw/fz/fzak52.pafc.cwf.alu.txt"
                response = self.session.get(text_url, timeout=10)
                if response.status_code == 200:
                    text_content = response.text
                    
                    # Parse the text to find PKZ766 section
                    if 'PKZ766' in text_content:
                        # Extract the PKZ766 section
                        lines = text_content.split('\n')
                        pkz766_content = []
                        in_pkz766 = False
                        
                        for i, line in enumerate(lines):
                            if 'PKZ766' in line:
                                in_pkz766 = True
                                pkz766_content.append(line)
                                continue
                            
                            if in_pkz766:
                                # Stop at next zone or $$ marker
                                if line.startswith('PKZ') and 'PKZ766' not in line:
                                    break
                                if line.strip() == '$$':
                                    break
                                pkz766_content.append(line)
                        
                        if pkz766_content:
                            marine_data['PKZ766'] = {
                                'name': 'Pribilof Islands Nearshore Waters',
                                'raw_text': '\n'.join(pkz766_content),
                                'source': text_url
                            }
                            logger.info("Successfully fetched PKZ766 marine forecast")
            except Exception as e:
                logger.warning(f"Could not fetch PKZ766 text product: {e}")
            
            return marine_data if marine_data else None
            
        except Exception as e:
            logger.error(f"Error getting marine forecast: {e}")
            return None
    
    def fetch_all_forecasts(self) -> Dict:
        """Fetch all forecasts for configured zip codes"""
        results = {}
        
        for zip_code in self.zip_codes:
            logger.info(f"Fetching forecast for zip code: {zip_code}")
            
            coords = self.get_coordinates_from_zip(zip_code)
            if not coords:
                logger.warning(f"Could not get coordinates for {zip_code}")
                continue
            
            zip_data = {
                'zip_code': zip_code,
                'location': coords['city'],
                'coordinates': {'lat': coords['lat'], 'lon': coords['lon']},
                'timestamp': datetime.utcnow().isoformat(),
                'local_forecast': None,
                'marine_forecast': None
            }
            
            # Get forecast URLs
            forecast_urls = self.get_forecast_urls(coords['lat'], coords['lon'])
            if forecast_urls and forecast_urls['forecast']:
                # Get local forecast
                local_forecast = self.get_forecast(forecast_urls['forecast'])
                if local_forecast:
                    zip_data['local_forecast'] = {
                        'updated': local_forecast.get('updated'),
                        'periods': local_forecast.get('periods', [])[:7]  # Next 7 periods
                    }
            
            # Get marine forecast
            marine_forecast = self.get_marine_forecast(coords['lat'], coords['lon'])
            if marine_forecast:
                zip_data['marine_forecast'] = marine_forecast
            
            results[zip_code] = zip_data
            
            # Be nice to the API
            time.sleep(1)
        
        return results
    
    def format_output(self, data: Dict) -> str:
        """Format the forecast data for display"""
        output = []
        output.append("=" * 80)
        output.append(f"WEATHER FORECAST REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 80)
        
        for zip_code, zip_data in data.items():
            output.append(f"\n{'='*80}")
            output.append(f"ZIP CODE: {zip_code} - {zip_data['location']}")
            output.append(f"Coordinates: {zip_data['coordinates']['lat']}, {zip_data['coordinates']['lon']}")
            output.append(f"{'='*80}")
            
            # Local Forecast
            if zip_data['local_forecast']:
                output.append(f"\n--- LOCAL FORECAST ---")
                output.append(f"Updated: {zip_data['local_forecast']['updated']}")
                for period in zip_data['local_forecast']['periods']:
                    output.append(f"\n{period['name']}:")
                    output.append(f"  Temperature: {period['temperature']}°{period['temperatureUnit']}")
                    output.append(f"  Wind: {period.get('windSpeed', 'N/A')} {period.get('windDirection', '')}")
                    output.append(f"  {period['detailedForecast']}")
            else:
                output.append(f"\n--- LOCAL FORECAST ---")
                output.append("No local forecast data available")
            
            # Marine Forecast
            if zip_data['marine_forecast']:
                output.append(f"\n--- MARINE FORECAST ---")
                for zone_id, zone_data in zip_data['marine_forecast'].items():
                    output.append(f"\nZone {zone_id}: {zone_data.get('name', 'Unknown')}")
                    if 'periods' in zone_data:
                        for period in zone_data['periods'][:3]:  # First 3 periods
                            output.append(f"  {period.get('name', 'N/A')}:")
                            output.append(f"    {period.get('detailedForecast', 'No details available')}")
            else:
                output.append(f"\n--- MARINE FORECAST ---")
                output.append("No marine forecast data available")
        
        output.append(f"\n{'='*80}\n")
        return "\n".join(output)


def main():
    """Main application entry point"""
    # Configuration
    zip_codes = os.getenv('ZIP_CODES', '99660,99591').split(',')
    update_interval = int(os.getenv('UPDATE_INTERVAL', '3600'))  # Default 1 hour
    
    logger.info(f"Starting Weather Forecast Application")
    logger.info(f"Monitoring zip codes: {', '.join(zip_codes)}")
    logger.info(f"Update interval: {update_interval} seconds")
    
    fetcher = WeatherForecastFetcher(zip_codes)
    
    while True:
        try:
            logger.info("Fetching weather forecasts...")
            forecasts = fetcher.fetch_all_forecasts()
            
            # Save combined forecast to file
            output_file = '/data/latest_forecast.json'
            with open(output_file, 'w') as f:
                json.dump(forecasts, f, indent=2)
            logger.info(f"Saved forecast data to {output_file}")
            
            # Save individual island forecasts
            marine_forecasts_combined = {}
            for zip_code, zip_data in forecasts.items():
                island_name = zip_data.get('location', zip_code).replace(' ', '_').lower()
                
                # Save individual JSON
                individual_json = f'/data/{island_name}_{zip_code}.json'
                with open(individual_json, 'w') as f:
                    json.dump(zip_data, f, indent=2)
                logger.info(f"Saved {zip_data.get('location')} data to {individual_json}")
                
                # Save individual formatted text
                individual_txt = f'/data/{island_name}_{zip_code}.txt'
                individual_formatted = fetcher.format_output({zip_code: zip_data})
                with open(individual_txt, 'w') as f:
                    f.write(individual_formatted)
                logger.info(f"Saved {zip_data.get('location')} formatted forecast to {individual_txt}")
                
                # Collect marine forecasts
                if zip_data.get('marine_forecast'):
                    for zone_id, zone_data in zip_data['marine_forecast'].items():
                        if zone_id not in marine_forecasts_combined:
                            marine_forecasts_combined[zone_id] = zone_data
            
            # Save separate marine forecast file
            if marine_forecasts_combined:
                marine_json = '/data/pribilof_island_waters.json'
                with open(marine_json, 'w') as f:
                    json.dump(marine_forecasts_combined, f, indent=2)
                logger.info(f"Saved marine forecast data to {marine_json}")
                
                # Format marine forecast text
                marine_txt = '/data/pribilof_island_waters.txt'
                marine_output = []
                marine_output.append("=" * 80)
                marine_output.append(f"PRIBILOF ISLANDS MARINE FORECAST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                marine_output.append("=" * 80)
                marine_output.append("")
                
                for zone_id, zone_data in marine_forecasts_combined.items():
                    marine_output.append(f"Zone {zone_id}: {zone_data.get('name', 'Unknown')}")
                    marine_output.append("-" * 80)
                    
                    # Check for raw text format (from text products)
                    if 'raw_text' in zone_data:
                        marine_output.append(zone_data['raw_text'])
                    # Check for structured periods format
                    elif 'periods' in zone_data and zone_data['periods']:
                        for period in zone_data['periods']:
                            marine_output.append(f"\n{period.get('name', 'N/A')}:")
                            marine_output.append(f"  {period.get('detailedForecast', 'No details available')}")
                    else:
                        marine_output.append("  No detailed forecast data available")
                    marine_output.append("")
                
                marine_output.append("=" * 80)
                
                with open(marine_txt, 'w') as f:
                    f.write("\n".join(marine_output))
                logger.info(f"Saved marine forecast text to {marine_txt}")
            
            # Print formatted output
            formatted = fetcher.format_output(forecasts)
            print(formatted)
            
            # Save combined formatted output
            text_output_file = '/data/latest_forecast.txt'
            with open(text_output_file, 'w') as f:
                f.write(formatted)
            logger.info(f"Saved combined formatted forecast to {text_output_file}")
            
            logger.info(f"Waiting {update_interval} seconds until next update...")
            time.sleep(update_interval)
            
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(60)  # Wait a minute before retrying


if __name__ == "__main__":
    main()
