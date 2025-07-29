# Week 14 Reflection: Custom Feature Overview

## Brief Description

### What is the custom feature?

This project features a custom predictive weather model that delivers advanced weather forecasts and
personalized activity recommendations. The system leverages real team-contributed data and integrates
machine learning to analyze historical weather and user activity, providing tailored suggestions and
interactive visualizations. The bonus feature is a generative poetry creator that creates up to three
styles of poetry based on the city weather being fetched by the API.

### How does it work?

The predictive model combines team weather data and user journal entries to train and update its
forecasts. Users can access enhanced weather predictions, compare cities, and receive activity
recommendations directly within the dashboard. The application uses both local and external data
sources, with results presented through dynamic charts and summary panels.

### Known Bugs & Next Steps

- There are known conflicts between `ttkbootstrap` and the custom sound MP3 files included in the
  project, which may affect sound playback.
- Occasional API delays can impact the responsiveness of weather updates.
- As a mitigation, an additional API source (weatherapi.com) has been integrated, and the number of
  custom sounds has been reduced for stability.
- Planned improvements include enhanced error handling, expanding supported activities, and further
  optimizing the predictive model for speed and accuracy.

---
