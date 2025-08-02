"""GitHub Team Service for fetching team weather data."""

import json
import csv
import io
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class TeamCityData:
    """Data class for team member city weather data."""
    member_name: str
    city_name: str
    country: str
    last_updated: str
    weather_data: Dict[str, Any]
    avatar_url: Optional[str] = None
    github_username: Optional[str] = None


class GitHubTeamService:
    """Service for managing team collaboration and city data from GitHub."""

    REPO_URL = "https://github.com/StrayDogSyn/New_Team_Dashboard"
    CSV_DATA_URL = "https://raw.githubusercontent.com/StrayDogSyn/New_Team_Dashboard/main/exports/team_weather_data.csv"

    def __init__(self, github_token: Optional[str] = None):
        """Initialize the GitHub team service."""
        self.team_data_cache = {}
        self.last_sync = None
        self.cache_duration = timedelta(minutes=15)  # Cache for 15 minutes
        self.cache_file = Path("data/team_cache.json")

        # GitHub token for API access
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')

        # Ensure data directory exists
        self.cache_file.parent.mkdir(exist_ok=True)

        # Load cached data on startup
        self._load_cached_data()

    def fetch_team_cities(self) -> List[TeamCityData]:
        """Fetch weather data from team members from CSV file."""
        try:
            # Check if we have recent cached data
            if self._is_cache_valid():
                logger.info("Using cached team data")
                return self._get_cached_team_data()

            logger.info(f"Fetching team data from {self.CSV_DATA_URL}")

            # Set up headers for GitHub API if token is available
            headers = {}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'

            response = requests.get(self.CSV_DATA_URL, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse CSV data
            team_cities = self._parse_csv_data(response.text)

            # Update cache
            self._save_team_cache(team_cities)
            self.last_sync = datetime.now()

            logger.info(f"Successfully fetched {len(team_cities)} team cities")
            return team_cities

        except requests.RequestException as e:
            logger.error(f"Failed to fetch team data from GitHub: {e}")
            return self._get_cached_team_data()
        except Exception as e:
            logger.error(f"Unexpected error fetching team data: {e}")
            return self._get_cached_team_data()

    def get_team_cities(self) -> List[TeamCityData]:
        """Get team cities data (alias for fetch_team_cities)."""
        return self.fetch_team_cities()

    def get_team_activity_feed(self) -> List[Dict[str, Any]]:
        """Get recent team activity feed."""
        team_cities = self.fetch_team_cities()
        activity_feed = []

        for city in team_cities:
            try:
                last_updated = datetime.fromisoformat(city.last_updated.replace('Z', '+00:00'))
                activity_feed.append({
                    "member": city.member_name,
                    "city": city.city_name,
                    "action": "updated weather data",
                    "timestamp": last_updated,
                    "weather": city.weather_data.get("description", "Unknown"),
                    "temperature": city.weather_data.get("temperature", "N/A")
                })
            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid timestamp for {city.member_name}: {e}")
                continue

        # Sort by timestamp, most recent first
        activity_feed.sort(key=lambda x: x["timestamp"], reverse=True)
        return activity_feed[:10]  # Return last 10 activities

    def _parse_csv_data(self, csv_text: str) -> List[TeamCityData]:
        """Parse CSV data and convert to TeamCityData objects."""
        team_cities = []

        try:
            # Create a StringIO object from the CSV text
            csv_file = io.StringIO(csv_text)
            csv_reader = csv.DictReader(csv_file)

            # Track unique member-city combinations to avoid duplicates
            seen_combinations = set()

            for row in csv_reader:
                try:
                    # Extract member name and city from CSV
                    member_name = row.get('member_name', 'Unknown Member')
                    city_name = row.get('city', 'Unknown City')
                    country = row.get('country', 'Unknown Country')

                    # Create unique key for this member-city combination
                    unique_key = f"{member_name}_{city_name}"
                    if unique_key in seen_combinations:
                        continue
                    seen_combinations.add(unique_key)

                    # Parse weather data from CSV columns
                    weather_data = {
                        'temperature': self._safe_float(row.get('temperature', 0)),
                        'humidity': self._safe_float(row.get('humidity', 0)),
                        'wind_speed': self._safe_float(row.get('wind_speed', 0)),
                        'description': row.get('weather_description', row.get('description', 'Unknown')),
                        'main': row.get('weather_main', 'Unknown'),
                        'pressure': self._safe_float(row.get('pressure', 0)),
                        'feels_like': self._safe_float(row.get('feels_like', 0)),
                        'visibility': self._safe_float(row.get('visibility', 0)),
                        'wind_direction': self._safe_float(row.get('wind_direction', 0))
                    }

                    # Parse timestamp
                    timestamp = row.get('timestamp', row.get('datetime', datetime.now().isoformat()))

                    # Create TeamCityData object
                    team_city = TeamCityData(
                        member_name=member_name,
                        city_name=city_name,
                        country=country,
                        last_updated=timestamp,
                        weather_data=weather_data,
                        avatar_url=None,  # Not available in CSV
                        github_username=member_name.lower().replace(' ', '_')  # Generate from name
                    )

                    team_cities.append(team_city)

                except Exception as row_error:
                    logger.warning(f"Error parsing CSV row: {row_error}")
                    continue

            logger.info(f"Parsed {len(team_cities)} unique team cities from CSV")
            return team_cities

        except Exception as e:
            logger.error(f"Error parsing CSV data: {e}")
            return []

    def _safe_float(self, value: Any) -> float:
        """Safely convert value to float, return 0.0 if conversion fails."""
        try:
            if value is None or value == '':
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def contribute_data(self, city_data: Dict[str, Any], github_token: Optional[str] = None) -> bool:
        """Add your city to team data (requires GitHub token for actual contribution)."""
        # For now, this is a placeholder that would create a pull request
        # In a real implementation, this would use GitHub API to create a PR
        logger.info(f"Would contribute data for {city_data.get('city', 'Unknown')}")

        if github_token:
            # Create headers for GitHub API
            headers = {
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            # Get the current file content
            current_file_url = f"https://api.github.com/repos/StrayDogSyn/New_Team_Dashboard/contents/exports/team_weather_data.csv"
            response = requests.get(current_file_url, headers=headers)
            response.raise_for_status()
            current_content = response.json()

            # Create a new branch
            branch_name = f"weather-update-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            main_branch = requests.get(
                "https://api.github.com/repos/StrayDogSyn/New_Team_Dashboard/git/refs/heads/main",
                headers=headers
            ).json()

            # Create new branch reference
            requests.post(
                "https://api.github.com/repos/StrayDogSyn/New_Team_Dashboard/git/refs",
                headers=headers,
                json={
                    "ref": f"refs/heads/{branch_name}",
                    "sha": main_branch['object']['sha']
                }
            ).raise_for_status()

            # Update file content
            new_content = self._update_csv_content(current_content['content'], city_data)

            # Create commit
            requests.put(
                current_file_url,
                headers=headers,
                json={
                    "message": f"Update weather data for {city_data.get('city', 'Unknown')}",
                    "content": new_content,
                    "sha": current_content['sha'],
                    "branch": branch_name
                }
            ).raise_for_status()

            # Create pull request
            pr_response = requests.post(
                "https://api.github.com/repos/StrayDogSyn/New_Team_Dashboard/pulls",
                headers=headers,
                json={
                    "title": f"Update weather data for {city_data.get('city', 'Unknown')}",
                    "body": "Automated weather data update",
                    "head": branch_name,
                    "base": "main"
                }
            )
            pr_response.raise_for_status()

            logger.info(f"Created PR #{pr_response.json()['number']} for {city_data.get('city', 'Unknown')}")
            return True
            pass

        return False  # Not implemented yet

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self.last_sync:
            return False

        return datetime.now() - self.last_sync < self.cache_duration

    def _get_cached_team_data(self) -> List[TeamCityData]:
        """Get team data from cache."""
        if not self.team_data_cache:
            return []

        team_cities = []
        for city_data in self.team_data_cache.get("cities", []):
            team_city = TeamCityData(
                member_name=city_data.get("member_name", "Unknown"),
                city_name=city_data.get("city_name", "Unknown"),
                country=city_data.get("country", "Unknown"),
                last_updated=city_data.get("last_updated", datetime.now().isoformat()),
                weather_data=city_data.get("weather_data", {}),
                avatar_url=city_data.get("avatar_url"),
                github_username=city_data.get("github_username")
            )
            team_cities.append(team_city)

        return team_cities

    def _save_team_cache(self, team_cities: List[TeamCityData]) -> None:
        """Save team data to cache."""
        try:
            cache_data = {
                "cities": [
                    {
                        "member_name": city.member_name,
                        "city_name": city.city_name,
                        "country": city.country,
                        "last_updated": city.last_updated,
                        "weather_data": city.weather_data,
                        "avatar_url": city.avatar_url,
                        "github_username": city.github_username
                    }
                    for city in team_cities
                ],
                "timestamp": datetime.now().isoformat()
            }

            self.team_data_cache = cache_data

            # Save to file
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved team cache with {len(team_cities)} cities")

        except Exception as e:
            logger.error(f"Failed to save team cache: {e}")

    def _load_cached_data(self) -> None:
        """Load cached data from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.team_data_cache = json.load(f)

                # Check if cache timestamp is valid
                cache_timestamp = self.team_data_cache.get("timestamp")
                if cache_timestamp:
                    self.last_sync = datetime.fromisoformat(cache_timestamp)
                    if not self._is_cache_valid():
                        self.last_sync = None

                logger.info("Loaded team data from cache")

        except Exception as e:
            logger.error(f"Failed to load cached data: {e}")
            self.team_data_cache = {}

    def force_refresh(self) -> List[TeamCityData]:
        """Force refresh team data, ignoring cache."""
        self.last_sync = None
        return self.fetch_team_cities()

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state."""
        return {
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "cache_valid": self._is_cache_valid(),
            "cached_cities_count": len(self.team_data_cache.get("cities", [])),
            "cache_file_exists": self.cache_file.exists()
        }
