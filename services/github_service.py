"""GitHub service for repository integration."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from github import Github, GithubException
except ImportError:
    Github = None
    GithubException = Exception

from config.settings import settings


class GitHubServiceError(Exception):
    """Custom exception for GitHub service errors."""
    pass


class GitHubService:
    """GitHub API service for repository operations."""
    
    def __init__(self):
        if not Github:
            raise GitHubServiceError(
                "PyGithub package not installed. "
                "Install with: pip install PyGithub"
            )
        
        if not settings.github_token:
            raise GitHubServiceError(
                "GITHUB_TOKEN not configured. "
                "Please set it in your .env file."
            )
        
        # Initialize GitHub client
        self.github = Github(settings.github_token)
        self._user = None
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        try:
            if not self._user:
                self._user = self.github.get_user()
            
            return {
                'login': self._user.login,
                'name': self._user.name or self._user.login,
                'avatar_url': self._user.avatar_url,
                'public_repos': self._user.public_repos,
                'followers': self._user.followers
            }
        except GithubException as e:
            raise GitHubServiceError(f"Failed to get user info: {e}")
    
    def get_repository(self, repo_name: str) -> Dict[str, Any]:
        """Get repository information."""
        try:
            # Try user's repo first, then public repo
            try:
                repo = self.github.get_user().get_repo(repo_name)
            except GithubException:
                repo = self.github.get_repo(repo_name)
            
            return {
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'language': repo.language,
                'updated_at': repo.updated_at.isoformat() if repo.updated_at else None,
                'html_url': repo.html_url
            }
        except GithubException as e:
            raise GitHubServiceError(f"Repository '{repo_name}' not found: {e}")
    
    def create_issue(self, repo_name: str, title: str, body: str) -> Dict[str, Any]:
        """Create an issue in a repository."""
        try:
            repo = self.github.get_user().get_repo(repo_name)
            issue = repo.create_issue(title=title, body=body)
            
            return {
                'number': issue.number,
                'title': issue.title,
                'html_url': issue.html_url,
                'created_at': issue.created_at.isoformat()
            }
        except GithubException as e:
            raise GitHubServiceError(f"Failed to create issue: {e}")
    
    def get_recent_commits(self, repo_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent commits from a repository."""
        try:
            repo = self.github.get_repo(repo_name)
            commits = repo.get_commits()[:limit]
            
            return [
                {
                    'sha': commit.sha[:8],
                    'message': commit.commit.message.split('\n')[0],
                    'author': commit.commit.author.name,
                    'date': commit.commit.author.date.isoformat(),
                    'html_url': commit.html_url
                }
                for commit in commits
            ]
        except GithubException as e:
            raise GitHubServiceError(f"Failed to get commits: {e}")
    
    def is_available(self) -> bool:
        """Check if GitHub service is properly configured and available."""
        return bool(Github and settings.github_token)
    
    def test_connection(self) -> bool:
        """Test GitHub API connection."""
        try:
            self.github.get_user().login
            return True
        except GithubException:
            return False