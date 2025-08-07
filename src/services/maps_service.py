"""Interactive Weather Maps Service.

Provides comprehensive weather mapping functionality including:
- Temperature heat maps
- Precipitation radar
- Wind speed vectors
- Weather stations
- Severe weather alerts
- Storm tracking
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

import folium
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim


@dataclass
class WeatherStation:
    """Weather station data."""

    id: str
    name: str
    latitude: float
    longitude: float
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    last_updated: Optional[datetime] = None
    data_freshness: str = "unknown"


@dataclass
class WeatherAlert:
    """Weather alert data."""

    id: str
    title: str
    description: str
    severity: str  # "minor", "moderate", "severe", "extreme"
    event_type: str  # "thunderstorm", "tornado", "flood", etc.
    start_time: datetime
    end_time: Optional[datetime]
    areas: List[Tuple[float, float]]  # List of (lat, lon) coordinates
    color: str = "#ff0000"


@dataclass
class StormTrack:
    """Storm tracking data."""

    id: str
    name: str
    category: str
    current_position: Tuple[float, float]
    forecast_path: List[Tuple[float, float, datetime]]
    wind_speed: float
    pressure: float
    movement_speed: float
    movement_direction: float


class WeatherMapsService:
    """Service for creating interactive weather maps."""

    def __init__(self, api_key: str, cache_dir: str = "cache/maps"):
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.geolocator = Nominatim(user_agent="weather_dashboard")

        # Cache for tile data and weather information
        self._tile_cache = {}
        self._weather_cache = {}
        self._cache_expiry = 600  # 10 minutes

        # Weather data URLs (using OpenWeatherMap as example)
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.tile_url = "https://tile.openweathermap.org/map"

    def create_interactive_map(
        self, center_lat: float = 40.7128, center_lon: float = -74.0060, zoom: int = 8
    ) -> folium.Map:
        """Create base interactive map with weather layers."""
        try:
            # Create base map
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=zoom,
                tiles="OpenStreetMap",
                control_scale=True,
            )

            # Add layer control
            folium.LayerControl().add_to(m)

            # Add click handler for weather data
            click_js = """
            function(e) {
                var lat = e.latlng.lat;
                var lng = e.latlng.lng;
                var popup = L.popup()
                    .setLatLng(e.latlng)
                    .setContent('Loading weather data...')
                    .openOn(this);

                // In a real implementation, this would make an API call
                setTimeout(function() {
                    popup.setContent(
                        '<b>Weather Data</b><br>' +
                        'Lat: ' + lat.toFixed(4) + '<br>' +
                        'Lng: ' + lng.toFixed(4) + '<br>' +
                        'Temperature: 22°C<br>' +
                        'Humidity: 65%<br>' +
                        'Wind: 15 km/h'
                    );
                }, 500);
            }
            """

            m.get_root().script.add_child(
                folium.Element(
                    f"""
                <script>
                    {{% macro script(this, kwargs) %}}
                        var map = {{{{ this.get_name() }}}};
                        map.on('click', {click_js});
                    {{% endmacro %}}
                </script>
                """
                )
            )

            return m

        except Exception as e:
            self.logger.error(f"Failed to create interactive map: {e}")
            raise

    def add_temperature_layer(self, map_obj: folium.Map, opacity: float = 0.6) -> folium.Map:
        """Add temperature heat map layer."""
        try:
            # Temperature tile layer from OpenWeatherMap
            temp_layer = folium.raster_layers.WmsTileLayer(
                url=f"{self.tile_url}/temp_new/{{z}}/{{x}}/{{y}}.png?appid={self.api_key}",
                layers="temp_new",
                name="Temperature",
                overlay=True,
                control=True,
                opacity=opacity,
                attr="OpenWeatherMap",
            )
            temp_layer.add_to(map_obj)

            # Add temperature legend
            legend_html = """
            <div style="position: fixed;
                        bottom: 50px; left: 50px; width: 150px; height: 90px;
                        background-color: white; border:2px solid grey; z-index:9999;
                        font-size:14px; padding: 10px">
            <p><b>Temperature (°C)</b></p>
            <p><i class="fa fa-square" style="color:#313695"></i> < -20</p>
            <p><i class="fa fa-square" style="color:#4575b4"></i> -20 to 0</p>
            <p><i class="fa fa-square" style="color:#fee090"></i> 0 to 20</p>
            <p><i class="fa fa-square" style="color:#d73027"></i> > 20</p>
            </div>
            """
            map_obj.get_root().html.add_child(folium.Element(legend_html))

            return map_obj

        except Exception as e:
            self.logger.error(f"Failed to add temperature layer: {e}")
            return map_obj

    def add_precipitation_layer(self, map_obj: folium.Map, opacity: float = 0.6) -> folium.Map:
        """Add precipitation radar layer."""
        try:
            # Precipitation tile layer
            precip_layer = folium.raster_layers.WmsTileLayer(
                url=f"{self.tile_url}/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={self.api_key}",
                layers="precipitation_new",
                name="Precipitation",
                overlay=True,
                control=True,
                opacity=opacity,
                attr="OpenWeatherMap",
            )
            precip_layer.add_to(map_obj)

            return map_obj

        except Exception as e:
            self.logger.error(f"Failed to add precipitation layer: {e}")
            return map_obj

    def add_wind_layer(self, map_obj: folium.Map, opacity: float = 0.6) -> folium.Map:
        """Add wind speed vectors layer."""
        try:
            # Wind tile layer
            wind_layer = folium.raster_layers.WmsTileLayer(
                url=f"{self.tile_url}/wind_new/{{z}}/{{x}}/{{y}}.png?appid={self.api_key}",
                layers="wind_new",
                name="Wind Speed",
                overlay=True,
                control=True,
                opacity=opacity,
                attr="OpenWeatherMap",
            )
            wind_layer.add_to(map_obj)

            return map_obj

        except Exception as e:
            self.logger.error(f"Failed to add wind layer: {e}")
            return map_obj

    def add_pressure_layer(self, map_obj: folium.Map, opacity: float = 0.6) -> folium.Map:
        """Add atmospheric pressure layer."""
        try:
            # Pressure tile layer
            pressure_layer = folium.raster_layers.WmsTileLayer(
                url=f"{self.tile_url}/pressure_new/{{z}}/{{x}}/{{y}}.png?appid={self.api_key}",
                layers="pressure_new",
                name="Pressure",
                overlay=True,
                control=True,
                opacity=opacity,
                attr="OpenWeatherMap",
            )
            pressure_layer.add_to(map_obj)

            return map_obj

        except Exception as e:
            self.logger.error(f"Failed to add pressure layer: {e}")
            return map_obj

    def add_clouds_layer(self, map_obj: folium.Map, opacity: float = 0.6) -> folium.Map:
        """Add cloud coverage layer."""
        try:
            # Clouds tile layer
            clouds_layer = folium.raster_layers.WmsTileLayer(
                url=f"{self.tile_url}/clouds_new/{{z}}/{{x}}/{{y}}.png?appid={self.api_key}",
                layers="clouds_new",
                name="Clouds",
                overlay=True,
                control=True,
                opacity=opacity,
                attr="OpenWeatherMap",
            )
            clouds_layer.add_to(map_obj)

            return map_obj

        except Exception as e:
            self.logger.error(f"Failed to add clouds layer: {e}")
            return map_obj

    async def get_weather_stations(
        self, lat: float, lon: float, radius: int = 50
    ) -> List[WeatherStation]:
        """Get nearby weather stations."""
        try:
            # Simulate weather stations data (in real implementation, use actual API)
            stations = [
                WeatherStation(
                    id="station_1",
                    name="Central Weather Station",
                    latitude=lat + 0.01,
                    longitude=lon + 0.01,
                    temperature=22.5,
                    humidity=65,
                    pressure=1013.2,
                    wind_speed=15.2,
                    wind_direction=180,
                    last_updated=datetime.now() - timedelta(minutes=5),
                    data_freshness="fresh",
                ),
                WeatherStation(
                    id="station_2",
                    name="Airport Weather Station",
                    latitude=lat - 0.02,
                    longitude=lon + 0.03,
                    temperature=21.8,
                    humidity=68,
                    pressure=1012.8,
                    wind_speed=18.5,
                    wind_direction=195,
                    last_updated=datetime.now() - timedelta(minutes=10),
                    data_freshness="recent",
                ),
            ]

            return stations

        except Exception as e:
            self.logger.error(f"Failed to get weather stations: {e}")
            return []

    def add_weather_stations_layer(
        self, map_obj: folium.Map, stations: List[WeatherStation]
    ) -> folium.Map:
        """Add weather stations to map."""
        try:
            # Create feature group for stations
            stations_group = folium.FeatureGroup(name="Weather Stations")

            for station in stations:
                # Color based on data freshness
                if station.data_freshness == "fresh":
                    color = "green"
                elif station.data_freshness == "recent":
                    color = "orange"
                else:
                    color = "red"

                # Create popup content
                popup_content = f"""
                <b>{station.name}</b><br>
                <b>Temperature:</b> {station.temperature}°C<br>
                <b>Humidity:</b> {station.humidity}%<br>
                <b>Pressure:</b> {station.pressure} hPa<br>
                <b>Wind:</b> {station.wind_speed} km/h @ {station.wind_direction}°<br>
                <b>Updated:</b> {station.last_updated.strftime('%H:%M:%S')}<br>
                <b>Freshness:</b> {station.data_freshness}
                """

                # Add station marker
                folium.CircleMarker(
                    location=[station.latitude, station.longitude],
                    radius=8,
                    popup=folium.Popup(popup_content, max_width=300),
                    color=color,
                    fillColor=color,
                    fillOpacity=0.7,
                    weight=2,
                ).add_to(stations_group)

            stations_group.add_to(map_obj)
            return map_obj

        except Exception as e:
            self.logger.error(f"Failed to add weather stations layer: {e}")
            return map_obj

    async def get_weather_alerts(self, lat: float, lon: float) -> List[WeatherAlert]:
        """Get active weather alerts for area."""
        try:
            # Simulate weather alerts (in real implementation, use actual API)
            alerts = [
                WeatherAlert(
                    id="alert_1",
                    title="Thunderstorm Warning",
                    description="Severe thunderstorms expected with heavy rain and strong winds.",
                    severity="severe",
                    event_type="thunderstorm",
                    start_time=datetime.now(),
                    end_time=datetime.now() + timedelta(hours=6),
                    areas=[
                        (lat - 0.1, lon - 0.1),
                        (lat + 0.1, lon - 0.1),
                        (lat + 0.1, lon + 0.1),
                        (lat - 0.1, lon + 0.1),
                    ],
                    color="#ff6600",
                )
            ]

            return alerts

        except Exception as e:
            self.logger.error(f"Failed to get weather alerts: {e}")
            return []

    def add_weather_alerts_layer(
        self, map_obj: folium.Map, alerts: List[WeatherAlert]
    ) -> folium.Map:
        """Add weather alerts to map."""
        try:
            # Create feature group for alerts
            alerts_group = folium.FeatureGroup(name="Weather Alerts")

            for alert in alerts:
                # Create alert polygon
                folium.Polygon(
                    locations=alert.areas,
                    color=alert.color,
                    fillColor=alert.color,
                    fillOpacity=0.3,
                    weight=2,
                    popup=folium.Popup(
                        f"<b>{alert.title}</b><br>{alert.description}<br>"
                        f"<b>Severity:</b> {alert.severity}",
                        max_width=300,
                    ),
                ).add_to(alerts_group)

            alerts_group.add_to(map_obj)
            return map_obj

        except Exception as e:
            self.logger.error(f"Failed to add weather alerts layer: {e}")
            return map_obj

    def add_drawing_tools(self, map_obj: folium.Map) -> folium.Map:
        """Add drawing tools for region selection."""
        try:
            # Add drawing plugin
            from folium.plugins import Draw

            draw = Draw(
                export=True,
                filename="region_data.geojson",
                position="topleft",
                draw_options={
                    "polyline": True,
                    "polygon": True,
                    "circle": True,
                    "rectangle": True,
                    "marker": True,
                    "circlemarker": False,
                },
                edit_options={"edit": True},
            )
            draw.add_to(map_obj)

            return map_obj

        except Exception as e:
            self.logger.error(f"Failed to add drawing tools: {e}")
            return map_obj

    def add_location_control(self, map_obj: folium.Map) -> folium.Map:
        """Add location control for current position."""
        try:
            # Add locate control plugin
            from folium.plugins import LocateControl

            locate_control = LocateControl(auto_start=False, flyTo=True, position="topleft")
            locate_control.add_to(map_obj)

            return map_obj

        except Exception as e:
            self.logger.error(f"Failed to add location control: {e}")
            return map_obj

    def add_measurement_tools(self, map_obj: folium.Map) -> folium.Map:
        """Add measurement tools."""
        try:
            # Add measurement plugin
            from folium.plugins import MeasureControl

            measure_control = MeasureControl(
                primary_length_unit="kilometers",
                secondary_length_unit="miles",
                primary_area_unit="sqkilometers",
                secondary_area_unit="acres",
            )
            measure_control.add_to(map_obj)

            return map_obj

        except Exception as e:
            self.logger.error(f"Failed to add measurement tools: {e}")
            return map_obj

    def geocode_location(self, location: str) -> Optional[Tuple[float, float]]:
        """Geocode location string to coordinates."""
        try:
            location_data = self.geolocator.geocode(location, timeout=10)
            if location_data:
                return (location_data.latitude, location_data.longitude)
            return None

        except GeocoderTimedOut:
            self.logger.warning(f"Geocoding timeout for location: {location}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to geocode location {location}: {e}")
            return None

    def create_comprehensive_weather_map(
        self,
        center_lat: float = 40.7128,
        center_lon: float = -74.0060,
        zoom: int = 8,
        include_all_layers: bool = True,
    ) -> folium.Map:
        """Create comprehensive weather map with all features."""
        try:
            # Create base map
            m = self.create_interactive_map(center_lat, center_lon, zoom)

            if include_all_layers:
                # Add all weather layers
                m = self.add_temperature_layer(m)
                m = self.add_precipitation_layer(m)
                m = self.add_wind_layer(m)
                m = self.add_pressure_layer(m)
                m = self.add_clouds_layer(m)

                # Add interactive tools
                m = self.add_drawing_tools(m)
                m = self.add_location_control(m)
                m = self.add_measurement_tools(m)

            return m

        except Exception as e:
            self.logger.error(f"Failed to create comprehensive weather map: {e}")
            raise

    def save_map(self, map_obj: folium.Map, filename: str) -> str:
        """Save map to HTML file."""
        try:
            filepath = self.cache_dir / filename
            map_obj.save(str(filepath))
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Failed to save map: {e}")
            raise
