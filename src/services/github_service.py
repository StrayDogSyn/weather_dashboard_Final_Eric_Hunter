"""GitHub integration service for team collaboration features.

This module provides GitHub API integration for sharing weather data and city comparisons
between team members, enabling collaborative weather analysis and data sharing.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
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

        # Initialize GitHub client
        self._initialize_github()

    def _initialize_github(self):
        """Initialize GitHub client and repository."""
        try:
            github_token = self.config.get_api_key("github")
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


def create_github_service(config_manager: ConfigManager) -> GitHubService:
    """Factory function to create GitHubService.

    Args:
        config_manager: Configuration manager instance

    Returns:
        GitHubService: Configured GitHub service instance
    """
    return GitHubService(config_manager)
