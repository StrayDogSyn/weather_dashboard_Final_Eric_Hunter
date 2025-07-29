# GitHub Team Data Integration

## Overview

The Weather Dashboard imports team weather data from GitHub repository **StrayDogSyn/New_Team_Dashboard** for the Compare Cities feature, with API fallback support.

## Features

- **Automatic Download**: GitHub data with local caching
- **Fallback Support**: API calls if GitHub unavailable
- **Team Data**: 200+ weather records from multiple team members
- **Multiple Cities**: 7+ cities with comprehensive data

## Available Cities

Austin TX, Providence RI, Rawlins WY, Ontario OR, New York NY, Miami FL, New Jersey

## Usage

1. **Compare Cities**: Navigate to Compare Cities tab, enter city names from available list
2. **Refresh Data**: Click "🔄 Refresh Team Data" button for manual refresh
3. **View Status**: Check data source and availability information

## Technical Details

**Data Sources**:
- Primary: GitHub repository `StrayDogSyn/New_Team_Dashboard`
- Fallback: OpenWeatherMap API

**Data Format**: CSV with fields: timestamp, member_name, city, temperature, humidity, wind_speed, weather_main

## Features

- **Team Insights**: Data attribution and collaborative analysis
- **Rich Comparisons**: Enhanced with team member observations

## Configuration

**Repository**: `StrayDogSyn/New_Team_Dashboard/main/exports`
**Local Storage**: `exports/` directory (auto-created)
**Files**: CSV and JSON data cached for offline use

## Troubleshooting

**Common Issues**:
- GitHub download fails → Check connection, falls back to sample data
- City not found → Use exact city names from available list
- Timestamp errors → Automatic format handling with fallback

**Resolution**: Use refresh button, check logs, API fallback available

---

For implementation details, see `src/services/team_data_service.py`
