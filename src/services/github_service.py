import requests
import json
from typing import Dict, List

class GitHubService:
    def __init__(self, repo_url: str = "https://github.com/StrayDogSyn/New_Team_Dashboard"):
        self.repo_url = repo_url
        self.api_base = "https://api.github.com"
        
    def get_team_weather_data(self) -> List[Dict]:
        """Fetch team weather data from GitHub."""
        # Get raw content from GitHub
        raw_url = self.repo_url.replace('github.com', 'raw.githubusercontent.com') + '/main/data/team_weather.json'
        
        response = requests.get(raw_url)
        if response.status_code == 200:
            return response.json()
        return []
        
    def contribute_weather_data(self, city_data: Dict, github_token: str):
        """Contribute weather data to team repository."""
        # This would require GitHub API authentication
        # Implementation depends on your team's workflow
        pass