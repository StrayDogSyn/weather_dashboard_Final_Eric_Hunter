"""GitHub integration service for team collaboration features.

This module provides GitHub API integration for sharing weather data and city comparisons
between team members, enabling collaborative weather analysis and data sharing.
"""

import json
import logging
import os
import urllib.request
import urllib.error
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from github import Github, GithubException
from github.Repository import Repository
from github.ContentFile import ContentFile

from ..core.config_manager import ConfigManager
from ..utils.logger import LoggerMixin


@dataclass
class TeamMember:
    """Team member information."""
    username: str
    name: str
    email: str
    role: str = "member"
    joined_at: str = ""
    last_active: str = ""
    cities_shared: int = 0
    contributions: int = 0


@dataclass
class CityData:
    """City weather data for sharing."""
    city_name: str
    country: str
    latitude: float
    longitude: float
    current_weather: Dict[str, Any]
    forecast_data: List[Dict[str, Any]]
    shared_by: str
    shared_at: str
    notes: str = ""
    tags: List[str] = None
    is_favorite: bool = False

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class TeamComparison:
    """Team city comparison data."""
    comparison_id: str
    title: str
    description: str
    cities: List[str]
    created_by: str
    created_at: str
    participants: List[str]
    metrics: List[str]  # temperature, humidity, wind_speed, etc.
    results: Dict[str, Any]
    is_public: bool = True


@dataclass
class ExportCityStats:
    """Statistics for a city from export data."""
    records: int
    temperature: Dict[str, Optional[float]]
    humidity: Dict[str, Optional[float]]
    wind: Dict[str, Optional[float]]
    weather_conditions: List[str]
    members: List[str]


@dataclass
class ExportTeamSummary:
    """Team summary from export data."""
    total_members: int
    total_cities: int
    total_records: int
    temperature_stats: Dict[str, float]
    humidity_stats: Dict[str, float]
    wind_stats: Dict[str, float]
    weather_conditions: List[str]
    countries: List[str]
    cities: List[str]
    members: List[str]


@dataclass
class ExportData:
    """Complete export data structure."""
    cities_analysis: Dict[str, Any]
    team_summary: ExportTeamSummary
    export_info: Dict[str, Any]
    raw_csv_data: Optional[List[Dict[str, Any]]] = None
    last_updated: str = ""
    fetch_timestamp: str = ""


class GitHubService(LoggerMixin):
    """GitHub service for team collaboration."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize GitHub service.

        Args:
            config_manager: Configuration manager instance
        """
        super().__init__()
        self.config = config_manager
        self.github = None
        self.repo = None
        self.team_repo_url = "https://github.com/StrayDogSyn/New_Team_Dashboard"
        self.data_branch = "weather-data"
        
        # Export data configuration
        self.export_base_url = "https://raw.githubusercontent.com/StrayDogSyn/New_Team_Dashboard/main/exports"
        self.export_data: Optional[ExportData] = None
        self.last_export_fetch = None
        self.export_refresh_interval = 300  # 5 minutes
        self.auto_refresh_enabled = True
        self.refresh_thread = None
        self.refresh_callbacks: List[Callable[[ExportData], None]] = []
        self._stop_refresh = threading.Event()

        # Initialize GitHub client
        self._initialize_github()
        
        # Start automatic export data fetching
        self._start_export_refresh()

    def _initialize_github(self):
        """Initialize GitHub client and repository."""
        try:
            github_token = self.config.api_config.github_token
            if not github_token:
                self.logger.warning("GitHub token not found. Team features will be limited.")
                return

            self.github = Github(github_token)

            # Parse repository from URL
            repo_path = self.team_repo_url.replace("https://github.com/", "")
            self.repo = self.github.get_repo(repo_path)

            # Verify access
            self.repo.get_contents("README.md")
            self.logger.info(f"Successfully connected to GitHub repository: {repo_path}")

        except GithubException as e:
            self.logger.error(f"GitHub authentication failed: {e}")
            self.github = None
            self.repo = None
        except Exception as e:
            self.logger.error(f"Error initializing GitHub service: {e}")
            self.github = None
            self.repo = None

    def is_connected(self) -> bool:
        """Check if GitHub service is connected and ready."""
        return self.github is not None and self.repo is not None

    def get_team_members(self) -> List[TeamMember]:
        """Get list of team members from repository."""
        if not self.is_connected():
            return []

        try:
            # Get contributors
            contributors = self.repo.get_contributors()
            members = []

            for contributor in contributors:
                member = TeamMember(
                    username=contributor.login,
                    name=contributor.name or contributor.login,
                    email=contributor.email or "",
                    contributions=contributor.contributions,
                    last_active=datetime.now().isoformat()
                )
                members.append(member)

            # Try to get additional member data from team file
            try:
                team_data = self._get_file_content("team/members.json")
                if team_data:
                    team_info = json.loads(team_data)
                    for member in members:
                        if member.username in team_info:
                            info = team_info[member.username]
                            member.role = info.get("role", "member")
                            member.joined_at = info.get("joined_at", "")
                            member.cities_shared = info.get("cities_shared", 0)
            except:
                pass  # Team file doesn't exist or is invalid

            self.logger.info(f"Retrieved {len(members)} team members")
            return members

        except Exception as e:
            self.logger.error(f"Error getting team members: {e}")
            return []

    def share_city_data(self, city_data: CityData) -> bool:
        """Share city weather data with the team.

        Args:
            city_data: City data to share

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            self.logger.error("GitHub service not connected")
            return False

        try:
            # Create file path
            safe_city_name = city_data.city_name.replace(" ", "_").replace(",", "")
            file_path = f"cities/{safe_city_name}_{city_data.country}.json"

            # Prepare data
            data = asdict(city_data)
            content = json.dumps(data, indent=2, ensure_ascii=False)

            # Check if file exists
            try:
                existing_file = self.repo.get_contents(file_path, ref=self.data_branch)
                # Update existing file
                self.repo.update_file(
                    path=file_path,
                    message=f"Update weather data for {city_data.city_name}",
                    content=content,
                    sha=existing_file.sha,
                    branch=self.data_branch
                )
                self.logger.info(f"Updated city data: {city_data.city_name}")
            except GithubException:
                # Create new file
                self.repo.create_file(
                    path=file_path,
                    message=f"Add weather data for {city_data.city_name}",
                    content=content,
                    branch=self.data_branch
                )
                self.logger.info(f"Created new city data: {city_data.city_name}")

            # Update team member stats
            self._update_member_stats(city_data.shared_by, "cities_shared")

            return True

        except Exception as e:
            self.logger.error(f"Error sharing city data: {e}")
            return False

    def get_shared_cities(self) -> List[CityData]:
        """Get all shared city data from the team.

        Returns:
            List[CityData]: List of shared city data
        """
        if not self.is_connected():
            return []

        try:
            cities = []

            # Get cities directory contents
            try:
                contents = self.repo.get_contents("cities", ref=self.data_branch)
            except GithubException:
                # Cities directory doesn't exist
                return []

            for content in contents:
                if content.type == "file" and content.name.endswith(".json"):
                    try:
                        file_content = self._get_file_content(content.path)
                        if file_content:
                            city_data = json.loads(file_content)
                            cities.append(CityData(**city_data))
                    except Exception as e:
                        self.logger.warning(f"Error parsing city file {content.name}: {e}")
                        continue

            self.logger.info(f"Retrieved {len(cities)} shared cities")
            return cities

        except Exception as e:
            self.logger.error(f"Error getting shared cities: {e}")
            return []

    def create_team_comparison(self, comparison: TeamComparison) -> bool:
        """Create a new team city comparison.

        Args:
            comparison: Team comparison data

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            return False

        try:
            # Create file path
            file_path = f"comparisons/{comparison.comparison_id}.json"

            # Prepare data
            data = asdict(comparison)
            content = json.dumps(data, indent=2, ensure_ascii=False)

            # Create file
            self.repo.create_file(
                path=file_path,
                message=f"Add team comparison: {comparison.title}",
                content=content,
                branch=self.data_branch
            )

            # Update member stats
            self._update_member_stats(comparison.created_by, "contributions")

            self.logger.info(f"Created team comparison: {comparison.title}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating team comparison: {e}")
            return False

    def get_team_comparisons(self) -> List[TeamComparison]:
        """Get all team comparisons.

        Returns:
            List[TeamComparison]: List of team comparisons
        """
        if not self.is_connected():
            return []

        try:
            comparisons = []

            # Get comparisons directory contents
            try:
                contents = self.repo.get_contents("comparisons", ref=self.data_branch)
            except GithubException:
                # Comparisons directory doesn't exist
                return []

            for content in contents:
                if content.type == "file" and content.name.endswith(".json"):
                    try:
                        file_content = self._get_file_content(content.path)
                        if file_content:
                            comparison_data = json.loads(file_content)
                            comparisons.append(TeamComparison(**comparison_data))
                    except Exception as e:
                        self.logger.warning(f"Error parsing comparison file {content.name}: {e}")
                        continue

            # Sort by creation date (newest first)
            comparisons.sort(key=lambda x: x.created_at, reverse=True)

            self.logger.info(f"Retrieved {len(comparisons)} team comparisons")
            return comparisons

        except Exception as e:
            self.logger.error(f"Error getting team comparisons: {e}")
            return []

    def update_comparison_results(self, comparison_id: str, results: Dict[str, Any]) -> bool:
        """Update results for a team comparison.

        Args:
            comparison_id: Comparison ID
            results: Updated results data

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            return False

        try:
            file_path = f"comparisons/{comparison_id}.json"

            # Get existing file
            existing_file = self.repo.get_contents(file_path, ref=self.data_branch)
            comparison_data = json.loads(existing_file.decoded_content.decode('utf-8'))

            # Update results
            comparison_data['results'] = results

            # Save updated data
            content = json.dumps(comparison_data, indent=2, ensure_ascii=False)
            self.repo.update_file(
                path=file_path,
                message=f"Update comparison results: {comparison_id}",
                content=content,
                sha=existing_file.sha,
                branch=self.data_branch
            )

            self.logger.info(f"Updated comparison results: {comparison_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating comparison results: {e}")
            return False

    def get_city_by_name(self, city_name: str, country: str = "") -> Optional[CityData]:
        """Get specific city data by name.

        Args:
            city_name: Name of the city
            country: Country code (optional)

        Returns:
            Optional[CityData]: City data if found, None otherwise
        """
        shared_cities = self.get_shared_cities()

        for city in shared_cities:
            if city.city_name.lower() == city_name.lower():
                if not country or city.country.lower() == country.lower():
                    return city

        return None

    def search_cities(self, query: str, limit: int = 10) -> List[CityData]:
        """Search shared cities by name or tags.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List[CityData]: Matching cities
        """
        shared_cities = self.get_shared_cities()
        results = []
        query_lower = query.lower()

        for city in shared_cities:
            # Search in city name, country, and tags
            if (query_lower in city.city_name.lower() or
                query_lower in city.country.lower() or
                any(query_lower in tag.lower() for tag in city.tags)):
                results.append(city)

                if len(results) >= limit:
                    break

        return results

    def get_team_activity(self, days: int = 7) -> Dict[str, Any]:
        """Get team activity statistics.

        Args:
            days: Number of days to look back

        Returns:
            Dict[str, Any]: Activity statistics
        """
        if not self.is_connected():
            return {}

        try:
            since = datetime.now() - timedelta(days=days)

            # Get recent commits
            commits = self.repo.get_commits(since=since, sha=self.data_branch)

            activity = {
                'total_commits': 0,
                'contributors': set(),
                'cities_added': 0,
                'comparisons_created': 0,
                'daily_activity': {}
            }

            for commit in commits:
                activity['total_commits'] += 1
                if commit.author:
                    activity['contributors'].add(commit.author.login)

                # Parse commit message for activity type
                message = commit.commit.message.lower()
                if 'add weather data' in message or 'update weather data' in message:
                    activity['cities_added'] += 1
                elif 'add team comparison' in message:
                    activity['comparisons_created'] += 1

                # Track daily activity
                date_str = commit.commit.author.date.strftime('%Y-%m-%d')
                if date_str not in activity['daily_activity']:
                    activity['daily_activity'][date_str] = 0
                activity['daily_activity'][date_str] += 1

            activity['contributors'] = list(activity['contributors'])

            return activity

        except Exception as e:
            self.logger.error(f"Error getting team activity: {e}")
            return {}

    def _get_file_content(self, file_path: str) -> Optional[str]:
        """Get content of a file from repository.

        Args:
            file_path: Path to the file

        Returns:
            Optional[str]: File content if found, None otherwise
        """
        try:
            file_content = self.repo.get_contents(file_path, ref=self.data_branch)
            return file_content.decoded_content.decode('utf-8')
        except GithubException:
            return None

    def _update_member_stats(self, username: str, stat_type: str):
        """Update team member statistics.

        Args:
            username: GitHub username
            stat_type: Type of statistic to update
        """
        try:
            # Get current team data
            team_data = {}
            try:
                content = self._get_file_content("team/members.json")
                if content:
                    team_data = json.loads(content)
            except:
                pass

            # Update member stats
            if username not in team_data:
                team_data[username] = {
                    "joined_at": datetime.now().isoformat(),
                    "cities_shared": 0,
                    "contributions": 0,
                    "role": "member"
                }

            if stat_type in team_data[username]:
                team_data[username][stat_type] += 1

            team_data[username]["last_active"] = datetime.now().isoformat()

            # Save updated data
            content = json.dumps(team_data, indent=2, ensure_ascii=False)

            try:
                existing_file = self.repo.get_contents("team/members.json", ref=self.data_branch)
                self.repo.update_file(
                    path="team/members.json",
                    message=f"Update member stats for {username}",
                    content=content,
                    sha=existing_file.sha,
                    branch=self.data_branch
                )
            except GithubException:
                self.repo.create_file(
                    path="team/members.json",
                    message=f"Create member stats for {username}",
                    content=content,
                    branch=self.data_branch
                )

        except Exception as e:
            self.logger.warning(f"Error updating member stats: {e}")

    def create_data_branch(self) -> bool:
        """Create the data branch if it doesn't exist.

        Returns:
            bool: True if successful or already exists, False otherwise
        """
        if not self.is_connected():
            return False

        try:
            # Check if branch exists
            try:
                self.repo.get_branch(self.data_branch)
                return True  # Branch already exists
            except GithubException:
                pass  # Branch doesn't exist, create it

            # Get main branch reference
            main_branch = self.repo.get_branch("main")

            # Create new branch
            self.repo.create_git_ref(
                ref=f"refs/heads/{self.data_branch}",
                sha=main_branch.commit.sha
            )

            self.logger.info(f"Created data branch: {self.data_branch}")
            return True

        except Exception as e:
            self.logger.error(f"Error creating data branch: {e}")
            return False

    # Export Data Fetching Methods
    
    def fetch_export_data(self, force_refresh: bool = False) -> Optional[ExportData]:
        """Fetch export data from the team dashboard repository.
        
        Args:
            force_refresh: Force refresh even if data is recent
            
        Returns:
            Optional[ExportData]: Export data if successful, None otherwise
        """
        # Check if we need to refresh
        if not force_refresh and self.export_data and self.last_export_fetch:
            time_since_fetch = datetime.now() - self.last_export_fetch
            if time_since_fetch.total_seconds() < self.export_refresh_interval:
                return self.export_data
        
        try:
            # Fetch JSON comparison data
            json_data = self._fetch_latest_json_export()
            if not json_data:
                return None
                
            # Fetch CSV raw data
            csv_data = self._fetch_latest_csv_export()
            
            # Parse and create ExportData
            export_data = self._parse_export_data(json_data, csv_data)
            
            if export_data:
                self.export_data = export_data
                self.last_export_fetch = datetime.now()
                self.export_data.fetch_timestamp = self.last_export_fetch.isoformat()
                
                # Notify callbacks
                self._notify_refresh_callbacks(export_data)
                
                self.logger.info("Successfully fetched export data")
                return export_data
                
        except Exception as e:
            self.logger.error(f"Error fetching export data: {e}")
            
        return None
    
    def _fetch_latest_json_export(self) -> Optional[Dict[str, Any]]:
        """Fetch the latest JSON export file.
        
        Returns:
            Optional[Dict[str, Any]]: JSON data if successful, None otherwise
        """
        try:
            # Try to find the latest export file
            # For now, use the known filename, but this could be enhanced to find the latest
            json_url = f"{self.export_base_url}/team_compare_cities_data_20250717_204218.json"
            
            with urllib.request.urlopen(json_url, timeout=30) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    self.logger.debug(f"Fetched JSON export from: {json_url}")
                    return data
                    
        except urllib.error.URLError as e:
            self.logger.error(f"URL error fetching JSON export: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching JSON export: {e}")
            
        return None
    
    def _fetch_latest_csv_export(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch the latest CSV export file.
        
        Returns:
            Optional[List[Dict[str, Any]]]: CSV data as list of dicts if successful, None otherwise
        """
        try:
            # Try to find the latest CSV export file
            csv_url = f"{self.export_base_url}/team_weather_data_20250717_204218.csv"
            
            with urllib.request.urlopen(csv_url, timeout=30) as response:
                if response.status == 200:
                    csv_content = response.read().decode('utf-8')
                    
                    # Parse CSV manually (simple implementation)
                    lines = csv_content.strip().split('\n')
                    if len(lines) < 2:
                        return None
                        
                    headers = [h.strip() for h in lines[0].split(',')]
                    data = []
                    
                    for line in lines[1:]:
                        if line.strip():
                            values = [v.strip() for v in line.split(',')]
                            if len(values) == len(headers):
                                row = dict(zip(headers, values))
                                data.append(row)
                    
                    self.logger.debug(f"Fetched CSV export with {len(data)} records from: {csv_url}")
                    return data
                    
        except urllib.error.URLError as e:
            self.logger.error(f"URL error fetching CSV export: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching CSV export: {e}")
            
        return None
    
    def _parse_export_data(self, json_data: Dict[str, Any], csv_data: Optional[List[Dict[str, Any]]]) -> Optional[ExportData]:
        """Parse raw export data into structured format.
        
        Args:
            json_data: Raw JSON data
            csv_data: Raw CSV data
            
        Returns:
            Optional[ExportData]: Parsed export data if successful, None otherwise
        """
        try:
            # Parse team summary
            team_summary_raw = json_data.get('team_summary', {})
            team_summary = ExportTeamSummary(
                total_members=team_summary_raw.get('total_members', 0),
                total_cities=team_summary_raw.get('total_cities', 0),
                total_records=team_summary_raw.get('total_records', 0),
                temperature_stats=team_summary_raw.get('temperature_stats', {}),
                humidity_stats=team_summary_raw.get('humidity_stats', {}),
                wind_stats=team_summary_raw.get('wind_stats', {}),
                weather_conditions=team_summary_raw.get('weather_conditions', []),
                countries=team_summary_raw.get('countries', []),
                cities=team_summary_raw.get('cities', []),
                members=team_summary_raw.get('members', [])
            )
            
            # Create export data
            export_data = ExportData(
                cities_analysis=json_data.get('cities_analysis', {}),
                team_summary=team_summary,
                export_info=json_data.get('export_info', {}),
                raw_csv_data=csv_data,
                last_updated=json_data.get('export_info', {}).get('export_date', ''),
                fetch_timestamp=datetime.now().isoformat()
            )
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"Error parsing export data: {e}")
            return None
    
    def _start_export_refresh(self):
        """Start the automatic export data refresh thread."""
        if not self.auto_refresh_enabled or self.refresh_thread:
            return
            
        def refresh_worker():
            """Worker function for automatic refresh."""
            while not self._stop_refresh.is_set():
                try:
                    # Initial fetch
                    self.fetch_export_data()
                    
                    # Wait for next refresh or stop signal
                    if self._stop_refresh.wait(self.export_refresh_interval):
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error in export refresh worker: {e}")
                    # Wait a bit before retrying
                    if self._stop_refresh.wait(60):
                        break
        
        self.refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
        self.refresh_thread.start()
        self.logger.info("Started export data auto-refresh")
    
    def stop_export_refresh(self):
        """Stop the automatic export data refresh."""
        if self.refresh_thread:
            self._stop_refresh.set()
            self.refresh_thread.join(timeout=5)
            self.refresh_thread = None
            self.logger.info("Stopped export data auto-refresh")
    
    def add_refresh_callback(self, callback: Callable[[ExportData], None]):
        """Add a callback to be notified when export data is refreshed.
        
        Args:
            callback: Function to call with new export data
        """
        self.refresh_callbacks.append(callback)
    
    def remove_refresh_callback(self, callback: Callable[[ExportData], None]):
        """Remove a refresh callback.
        
        Args:
            callback: Function to remove
        """
        if callback in self.refresh_callbacks:
            self.refresh_callbacks.remove(callback)
    
    def _notify_refresh_callbacks(self, export_data: ExportData):
        """Notify all registered callbacks of new export data.
        
        Args:
            export_data: New export data
        """
        for callback in self.refresh_callbacks:
            try:
                callback(export_data)
            except Exception as e:
                self.logger.error(f"Error in refresh callback: {e}")
    
    def get_export_data(self) -> Optional[ExportData]:
        """Get the current export data.
        
        Returns:
            Optional[ExportData]: Current export data if available, None otherwise
        """
        if not self.export_data:
            # Try to fetch if not available
            return self.fetch_export_data()
        return self.export_data
    
    def get_city_comparison_data(self) -> Dict[str, Any]:
        """Get city comparison data from exports.
        
        Returns:
            Dict[str, Any]: City comparison data
        """
        export_data = self.get_export_data()
        if export_data:
            return export_data.cities_analysis
        return {}
    
    def get_team_statistics(self) -> Optional[ExportTeamSummary]:
        """Get team statistics from exports.
        
        Returns:
            Optional[ExportTeamSummary]: Team statistics if available, None otherwise
        """
        export_data = self.get_export_data()
        if export_data:
            return export_data.team_summary
        return None
    
    def get_raw_weather_records(self) -> List[Dict[str, Any]]:
        """Get raw weather records from CSV export.
        
        Returns:
            List[Dict[str, Any]]: Raw weather records
        """
        export_data = self.get_export_data()
        if export_data and export_data.raw_csv_data:
            return export_data.raw_csv_data
        return []
    
    def set_refresh_interval(self, seconds: int):
        """Set the export data refresh interval.
        
        Args:
            seconds: Refresh interval in seconds
        """
        self.export_refresh_interval = max(60, seconds)  # Minimum 1 minute
        self.logger.info(f"Set export refresh interval to {self.export_refresh_interval} seconds")
    
    def enable_auto_refresh(self, enabled: bool = True):
        """Enable or disable automatic export data refresh.
        
        Args:
            enabled: Whether to enable auto-refresh
        """
        if enabled and not self.auto_refresh_enabled:
            self.auto_refresh_enabled = True
            self._start_export_refresh()
        elif not enabled and self.auto_refresh_enabled:
            self.auto_refresh_enabled = False
            self.stop_export_refresh()
    
    def cleanup(self):
        """Cleanup resources when service is destroyed."""
        self.stop_export_refresh()


def create_github_service(config_manager: ConfigManager) -> GitHubService:
    """Factory function to create GitHubService.

    Args:
        config_manager: Configuration manager instance

    Returns:
        GitHubService: Configured GitHub service instance
    """
    return GitHubService(config_manager)
