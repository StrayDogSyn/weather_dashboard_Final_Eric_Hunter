"""AI services module.

Provides AI-powered features including:
- Activity suggestions
- Weather analysis
- Machine learning models
"""

from .gemini_service import ActivityService

__all__ = [
    "ActivityService",
]