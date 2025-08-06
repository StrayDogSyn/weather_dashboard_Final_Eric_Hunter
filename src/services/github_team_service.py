"""GitHub Team Service for fetching team weather data."""

import csv
import io
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

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
    CSV_DATA_URL = (
        "https://raw.githubusercontent.com/StrayDogSyn/New_Team_Dashboard/"
        "main/exports/team_weather_data.csv"
    )

    def __init__(self, github_token: Optional[str] = None, repo: str = None):
        """Initialize the GitHub team service."""
        self.team_data_cache = {}
        self.last_sync = None
        self.cache_duration = timedelta(minutes=15)  # Cache for 15 minutes
        self.cache_file = Path("data/team_cache.json")

        # GitHub token for API access
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.repo = repo or os.getenv("GITHUB_REPO", "StrayDogSyn/New_Team_Dashboard")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.github_token}" if self.github_token else None,
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        self.username = os.getenv("GITHUB_USERNAME", "anonymous")

        # Ensure data directory exists
        self.cache_file.parent.mkdir(exist_ok=True)

        # Load cached data on startup
        self._load_cached_data()
        
    def is_configured(self) -> bool:
        """Check if GitHub integration is properly configured."""
        return bool(self.github_token and self.repo)
        
    def test_connection(self) -> bool:
        """Test GitHub API connection."""
        if not self.is_configured():
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/repos/{self.repo}",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"GitHub connection test failed: {e}")
            return False
            
    def push_weather_data(self, city: str, weather_data: dict) -> bool:
        """Push local weather data to team repository."""
        if not self.is_configured():
            logger.warning("GitHub integration not configured")
            return False
            
        try:
            file_path = f"data/weather/{city.lower().replace(' ', '_')}_weather.json"
            
            # Get current file content (if exists)
            current_data = self._get_file_content(file_path)
            
            # Prepare updated data
            updated_data = {
                "city": city,
                "last_updated": datetime.now().isoformat(),
                "contributor": self.username,
                "location": {
                    "name": city,
                    "coordinates": weather_data.get("coordinates", {})
                },
                "weather": {
                    "temperature": weather_data.get("temperature"),
                    "condition": weather_data.get("condition"),
                    "humidity": weather_data.get("humidity"),
                    "wind_speed": weather_data.get("wind_speed"),
                    "wind_direction": weather_data.get("wind_direction"),
                    "pressure": weather_data.get("pressure"),
                    "visibility": weather_data.get("visibility"),
                    "uv_index": weather_data.get("uv_index"),
                    "timestamp": datetime.now().isoformat()
                },
                "forecast": weather_data.get("forecast", []),
                "metadata": {
                    "source": "weather_dashboard",
                    "version": "1.0",
                    "api_source": weather_data.get("source", "unknown")
                }
            }
            
            # Add historical data if current data exists
            if current_data and isinstance(current_data, dict):
                if "history" not in updated_data:
                    updated_data["history"] = []
                    
                # Add previous reading to history
                if "weather" in current_data:
                    historical_entry = {
                        "timestamp": current_data.get("last_updated"),
                        "weather": current_data["weather"],
                        "contributor": current_data.get("contributor")
                    }
                    updated_data["history"].append(historical_entry)
                    
                # Keep only last 24 hours of history
                if len(updated_data["history"]) > 24:
                    updated_data["history"] = updated_data["history"][-24:]
                    
            # Push update to GitHub
            success = self._update_file(file_path, updated_data)
            
            if success:
                logger.info(f"Successfully pushed weather data for {city} to GitHub")
                # Also update team summary
                self._update_team_summary()
            else:
                logger.error(f"Failed to push weather data for {city} to GitHub")
                
            return success
            
        except Exception as e:
            logger.error(f"Error pushing weather data to GitHub: {e}")
            return False
            
    def get_team_weather_data(self) -> List[Dict]:
        """Fetch all team weather data from repository."""
        if not self.is_configured():
            return []
            
        try:
            # Get contents of weather data directory
            contents = self._get_directory_contents("data/weather")
            team_data = []
            
            for file_info in contents:
                if file_info["name"].endswith("_weather.json"):
                    file_data = self._get_file_content(file_info["path"])
                    if file_data:
                        team_data.append(file_data)
                        
            # Sort by last updated (most recent first)
            team_data.sort(
                key=lambda x: x.get("last_updated", ""),
                reverse=True
            )
            
            return team_data
            
        except Exception as e:
            logger.error(f"Error fetching team weather data: {e}")
            return []

    def fetch_team_data(self) -> List[Dict[str, Any]]:
        """Fetch team weather data from GitHub with proper error handling"""
        try:
            # Construct the raw content URL
            base_url = "https://raw.githubusercontent.com/StrayDogSyn/New_Team_Dashboard/main/"
            
            # Try multiple file formats
            team_data = []
            
            # Try JSON first
            try:
                json_url = base_url + "team_weather_data.json"
                response = requests.get(json_url, timeout=10)
                if response.status_code == 200:
                    team_data = response.json()
                    logger.info(f"Loaded {len(team_data)} entries from JSON")
            except Exception as e:
                logger.warning(f"JSON load failed: {e}")
            
            # Try CSV as fallback
            if not team_data:
                try:
                    csv_url = base_url + "team_weather_data.csv"
                    response = requests.get(csv_url, timeout=10)
                    if response.status_code == 200:
                        team_data = self._parse_csv_data(response.text)
                        logger.info(f"Loaded {len(team_data)} entries from CSV")
                except Exception as e:
                    logger.warning(f"CSV load failed: {e}")
            
            # Validate and clean data
            valid_data = []
            for entry in team_data:
                if self._validate_entry(entry):
                    valid_data.append(entry)
            
            # Cache the data
            self._cache_data(valid_data)
            
            return valid_data
            
        except Exception as e:
            logger.error(f"Failed to fetch team data: {e}")
            # Return cached data if available
            return self._get_cached_data()

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
                headers["Authorization"] = f"token {self.github_token}"

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
                last_updated = datetime.fromisoformat(city.last_updated.replace("Z", "+00:00"))
                activity_feed.append(
                    {
                        "member": city.member_name,
                        "city": city.city_name,
                        "action": "updated weather data",
                        "timestamp": last_updated,
                        "weather": city.weather_data.get("description", "Unknown"),
                        "temperature": city.weather_data.get("temperature", "N/A"),
                    }
                )
            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid timestamp for {city.member_name}: {e}")
                continue

        # Sort by timestamp, most recent first
        activity_feed.sort(key=lambda x: x["timestamp"], reverse=True)
        return activity_feed[:10]  # Return last 10 activities

    def _validate_entry(self, entry: Dict[str, Any]) -> bool:
        """Validate a team data entry"""
        required_fields = ['city', 'temperature', 'timestamp']
        
        # Check required fields
        for field in required_fields:
            if field not in entry:
                return False
        
        # Validate data types
        try:
            float(entry.get('temperature', 0))
            # Validate timestamp
            if 'timestamp' in entry:
                datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            return True
        except (ValueError, TypeError):
            return False

    def _get_cached_data(self) -> List[Dict[str, Any]]:
        """Get cached team data as fallback"""
        cache_file = Path('cache/team_weather_cache.json')
        try:
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
        
        # Return demo data if no cache
        return self._get_demo_data()

    def _cache_data(self, data: List[Dict[str, Any]]) -> None:
        """Cache team data for fallback use"""
        try:
            cache_file = Path('cache/team_weather_cache.json')
            cache_file.parent.mkdir(exist_ok=True)
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Cached {len(data)} team data entries")
        except Exception as e:
            logger.error(f"Failed to cache data: {e}")

    def _get_demo_data(self) -> List[Dict[str, Any]]:
        """Return demo data when no cache is available"""
        return [
            {
                "city": "New York",
                "temperature": 22.5,
                "timestamp": datetime.now().isoformat(),
                "member_name": "Demo User 1",
                "weather_description": "Partly cloudy"
            },
            {
                "city": "London",
                "temperature": 18.0,
                "timestamp": datetime.now().isoformat(),
                "member_name": "Demo User 2",
                "weather_description": "Light rain"
            },
            {
                "city": "Tokyo",
                "temperature": 25.3,
                "timestamp": datetime.now().isoformat(),
                "member_name": "Demo User 3",
                "weather_description": "Clear sky"
            }
        ]

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
                    member_name = row.get("member_name", "Unknown Member")
                    city_name = row.get("city", "Unknown City")
                    country = row.get("country", "Unknown Country")

                    # Create unique key for this member-city combination
                    unique_key = f"{member_name}_{city_name}"
                    if unique_key in seen_combinations:
                        continue
                    seen_combinations.add(unique_key)

                    # Parse weather data from CSV columns
                    weather_data = {
                        "temperature": self._safe_float(row.get("temperature", 0)),
                        "humidity": self._safe_float(row.get("humidity", 0)),
                        "wind_speed": self._safe_float(row.get("wind_speed", 0)),
                        "description": row.get(
                            "weather_description", row.get("description", "Unknown")
                        ),
                        "main": row.get("weather_main", "Unknown"),
                        "pressure": self._safe_float(row.get("pressure", 0)),
                        "feels_like": self._safe_float(row.get("feels_like", 0)),
                        "visibility": self._safe_float(row.get("visibility", 0)),
                        "wind_direction": self._safe_float(row.get("wind_direction", 0)),
                    }

                    # Parse timestamp
                    timestamp = row.get(
                        "timestamp", row.get("datetime", datetime.now().isoformat())
                    )

                    # Create TeamCityData object
                    team_city = TeamCityData(
                        member_name=member_name,
                        city_name=city_name,
                        country=country,
                        last_updated=timestamp,
                        weather_data=weather_data,
                        avatar_url=None,  # Not available in CSV
                        github_username=member_name.lower().replace(" ", "_"),  # Generate from name
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
            if value is None or value == "":
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def contribute_data(
        self, city_data: Dict[str, Any], github_token: Optional[str] = None
    ) -> bool:
        """Add your city to team data (requires GitHub token for actual contribution)."""
        # For now, this is a placeholder that would create a pull request
        # In a real implementation, this would use GitHub API to create a PR
        logger.info(f"Would contribute data for {city_data.get('city', 'Unknown')}")

        if github_token:
            # Create headers for GitHub API
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            # Get the current file content
            current_file_url = (
                "https://api.github.com/repos/StrayDogSyn/New_Team_Dashboard/"
                "contents/exports/team_weather_data.csv"
            )
            response = requests.get(current_file_url, headers=headers)
            response.raise_for_status()
            current_content = response.json()

            # Create a new branch
            branch_name = f"weather-update-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            main_branch = requests.get(
                "https://api.github.com/repos/StrayDogSyn/New_Team_Dashboard/git/refs/heads/main",
                headers=headers,
            ).json()

            # Create new branch reference
            requests.post(
                "https://api.github.com/repos/StrayDogSyn/New_Team_Dashboard/git/refs",
                headers=headers,
                json={"ref": f"refs/heads/{branch_name}", "sha": main_branch["object"]["sha"]},
            ).raise_for_status()

            # Update file content
            new_content = self._update_csv_content(current_content["content"], city_data)

            # Create commit
            requests.put(
                current_file_url,
                headers=headers,
                json={
                    "message": f"Update weather data for {city_data.get('city', 'Unknown')}",
                    "content": new_content,
                    "sha": current_content["sha"],
                    "branch": branch_name,
                },
            ).raise_for_status()

            # Create pull request
            pr_response = requests.post(
                "https://api.github.com/repos/StrayDogSyn/New_Team_Dashboard/pulls",
                headers=headers,
                json={
                    "title": f"Update weather data for {city_data.get('city', 'Unknown')}",
                    "body": "Automated weather data update",
                    "head": branch_name,
                    "base": "main",
                },
            )
            pr_response.raise_for_status()

            logger.info(
                f"Created PR #{pr_response.json()['number']} for {city_data.get('city', 'Unknown')}"
            )
            return True

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
                github_username=city_data.get("github_username"),
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
                        "github_username": city.github_username,
                    }
                    for city in team_cities
                ],
                "timestamp": datetime.now().isoformat(),
            }

            self.team_data_cache = cache_data

            # Save to file
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved team cache with {len(team_cities)} cities")

        except Exception as e:
            logger.error(f"Failed to save team cache: {e}")

    def _load_cached_data(self) -> None:
        """Load cached data from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
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
            "cache_file_exists": self.cache_file.exists(),
        }
        
    def _get_file_content(self, file_path: str) -> Optional[Dict]:
        """Get content of a file from the repository."""
        if not self.is_configured():
            return None
            
        try:
            url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                file_info = response.json()
                from base64 import b64decode
                content = b64decode(file_info["content"]).decode("utf-8")
                return json.loads(content)
            elif response.status_code == 404:
                return None  # File doesn't exist
            else:
                logger.error(f"Error fetching file {file_path}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting file content: {e}")
            return None
            
    def _update_file(self, file_path: str, data: Dict) -> bool:
        """Update or create a file in the repository."""
        if not self.is_configured():
            return False
            
        try:
            # Get current file info (for SHA if file exists)
            url = f"{self.base_url}/repos/{self.repo}/contents/{file_path}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            sha = None
            if response.status_code == 200:
                sha = response.json()["sha"]
                
            # Prepare content
            content = json.dumps(data, indent=2, ensure_ascii=False)
            from base64 import b64encode
            encoded_content = b64encode(content.encode("utf-8")).decode("utf-8")
            
            # Prepare commit data
            commit_data = {
                "message": f"Update weather data for {data.get('city', 'unknown location')}",
                "content": encoded_content,
                "committer": {
                    "name": self.username,
                    "email": f"{self.username}@weather-dashboard.local"
                }
            }
            
            if sha:
                commit_data["sha"] = sha
                
            # Make the commit
            response = requests.put(url, headers=self.headers, json=commit_data, timeout=15)
            
            if response.status_code in [200, 201]:
                return True
            else:
                logger.error(f"Error updating file: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating file: {e}")
            return False
            
    def _get_directory_contents(self, directory_path: str) -> List[Dict]:
        """Get contents of a directory in the repository."""
        if not self.is_configured():
            return []
            
        try:
            url = f"{self.base_url}/repos/{self.repo}/contents/{directory_path}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # Directory doesn't exist
                return []
            else:
                logger.error(f"Error getting directory contents: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting directory contents: {e}")
            return []
            
    def _update_team_summary(self) -> bool:
        """Update team weather summary file."""
        try:
            team_data = self.get_team_weather_data()
            
            summary = {
                "last_updated": datetime.now().isoformat(),
                "total_locations": len(team_data),
                "contributors": list(set(data.get("contributor", "unknown") for data in team_data)),
                "locations": []
            }
            
            for data in team_data:
                location_summary = {
                    "city": data.get("city"),
                    "contributor": data.get("contributor"),
                    "last_updated": data.get("last_updated"),
                    "current_weather": {
                        "temperature": data.get("weather", {}).get("temperature"),
                        "condition": data.get("weather", {}).get("condition")
                    }
                }
                summary["locations"].append(location_summary)
                
            return self._update_file("data/team_summary.json", summary)
            
        except Exception as e:
            logger.error(f"Error updating team summary: {e}")
            return False
            
    def get_team_summary(self) -> Optional[Dict]:
        """Get team weather summary."""
        return self._get_file_content("data/team_summary.json")
        
    def get_contributor_stats(self) -> Dict:
        """Get statistics about team contributors."""
        try:
            team_data = self.get_team_weather_data()
            stats = {
                "total_contributors": 0,
                "total_locations": len(team_data),
                "contributors": {},
                "most_active": None,
                "recent_activity": []
            }
            
            contributor_counts = {}
            recent_updates = []
            
            for data in team_data:
                contributor = data.get("contributor", "unknown")
                contributor_counts[contributor] = contributor_counts.get(contributor, 0) + 1
                
                recent_updates.append({
                    "contributor": contributor,
                    "city": data.get("city"),
                    "timestamp": data.get("last_updated")
                })
                
            stats["total_contributors"] = len(contributor_counts)
            stats["contributors"] = contributor_counts
            
            if contributor_counts:
                stats["most_active"] = max(contributor_counts.items(), key=lambda x: x[1])
                
            # Sort recent activity by timestamp
            recent_updates.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            stats["recent_activity"] = recent_updates[:10]  # Last 10 updates
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting contributor stats: {e}")
            return {}
