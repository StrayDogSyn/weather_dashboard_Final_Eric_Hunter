"""Machine Learning Weather Service for advanced analytics and recommendations."""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Conditional imports with fallback
try:
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.neighbors import NearestNeighbors
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Required ML libraries (scikit-learn, pandas, numpy, matplotlib) not available. ML features will be limited.")
    # Create dummy classes for type hints
    class np:
        ndarray = object
    class pd:
        DataFrame = object
    class plt:
        Figure = object
        @staticmethod
        def subplots(*args, **kwargs):
            return None, None
        @staticmethod
        def show():
            pass

from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WeatherProfile:
    """Weather profile for ML analysis."""

    city_name: str
    temperature: float
    humidity: float
    wind_speed: float
    pressure: float
    uv_index: float = 0.0
    visibility: float = 10.0
    feels_like: float = 0.0
    is_team_member: bool = False
    member_name: Optional[str] = None


@dataclass
class SimilarityResult:
    """Result of city similarity analysis."""

    city1: str
    city2: str
    similarity_score: float
    dominant_factors: List[str]
    recommendation: str


@dataclass
class ClusterResult:
    """Result of weather clustering analysis."""

    cluster_id: int
    cluster_name: str
    cities: List[str]
    characteristics: Dict[str, float]
    emoji: str
    description: str


@dataclass
class RecommendationResult:
    """City recommendation result."""

    recommended_city: str
    match_percentage: float
    reasons: List[str]
    cluster_info: ClusterResult
    comparison_data: Dict[str, Any]


class MLWeatherService:
    """Advanced ML-powered weather analysis service."""

    def __init__(self):
        """Initialize ML Weather Service with error handling for missing dependencies."""
        try:
            # Initialize sklearn components only if available
            if SKLEARN_AVAILABLE:
                self.scaler = StandardScaler()
                self.pca = None  # Will be initialized dynamically based on data
                self.kmeans = KMeans(n_clusters=5, random_state=42)
                self.nn_model = NearestNeighbors(n_neighbors=5, metric="cosine")
                self.ml_enabled = True
                logger.info("ML components initialized successfully")
            else:
                # Fallback: Initialize as None when sklearn is not available
                self.scaler = None
                self.pca = None
                self.kmeans = None
                self.nn_model = None
                self.ml_enabled = False
                logger.warning("ML components disabled due to missing sklearn")

            # Weather feature weights for different analysis types
            self.similarity_weights = {
                "temperature": 0.3,
                "humidity": 0.2,
                "wind_speed": 0.2,
                "pressure": 0.15,
                "uv_index": 0.1,
                "visibility": 0.05,
            }

            # Cluster characteristics
            self.cluster_profiles = {
                0: {
                    "name": "Mild & Cloudy",
                    "emoji": "☁️",
                    "desc": "Comfortable temperatures with moderate humidity",
                },
                1: {"name": "Dry Heat", "emoji": "🔥", "desc": "High temperatures with low humidity"},
                2: {
                    "name": "Storm Watch",
                    "emoji": "🌧️",
                    "desc": "High humidity with variable conditions",
                },
                3: {
                    "name": "Cool & Crisp",
                    "emoji": "❄️",
                    "desc": "Low temperatures with clear conditions",
                },
                4: {"name": "Tropical", "emoji": "🌴", "desc": "Warm and humid conditions"},
            }

            # Initialize cache for performance
            self._similarity_cache = {}
            self._cluster_cache = {}
            
            # Initialize ML prediction components
            if SKLEARN_AVAILABLE:
                self.models_dir = Path("models")
                self.models_dir.mkdir(exist_ok=True)
                self.prediction_models = {}
                self.prediction_scalers = {}
                self.feature_names = [
                    'temperature', 'humidity', 'pressure', 'wind_speed',
                    'hour', 'day_of_week', 'month', 'clouds', 'visibility'
                ]
                self.load_or_train_models()
            
            logger.info(f"ML Weather Service initialized (ML enabled: {self.ml_enabled})")
            
        except Exception as e:
            logger.error(f"Error initializing ML Weather Service: {e}")
            # Ensure service can still function with basic features
            self.ml_enabled = False
            self.scaler = None
            self.pca = None
            self.kmeans = None
            self.nn_model = None
            self._similarity_cache = {}
            self._cluster_cache = {}
            self.prediction_models = {}
            self.prediction_scalers = {}

    def prepare_weather_data(self, weather_profiles: List[WeatherProfile]) -> pd.DataFrame:
        """Prepare weather data for ML analysis."""
        try:
            data = []
            for profile in weather_profiles:
                data.append(
                    {
                        "city_name": profile.city_name,
                        "temperature": profile.temperature,
                        "humidity": profile.humidity,
                        "wind_speed": profile.wind_speed,
                        "pressure": profile.pressure,
                        "uv_index": profile.uv_index,
                        "visibility": profile.visibility,
                        "feels_like": profile.feels_like or profile.temperature,
                        "is_team_member": profile.is_team_member,
                        "member_name": profile.member_name,
                    }
                )

            df = pd.DataFrame(data)

            # Handle missing values
            numeric_columns = [
                "temperature",
                "humidity",
                "wind_speed",
                "pressure",
                "uv_index",
                "visibility",
                "feels_like",
            ]
            df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].mean())

            logger.info(f"Prepared weather data for {len(df)} cities")
            return df

        except Exception as e:
            logger.error(f"Error preparing weather data: {e}")
            return pd.DataFrame()

    def calculate_similarity_matrix(self, weather_profiles: List[WeatherProfile]) -> np.ndarray:
        """Calculate similarity matrix between cities using cosine similarity."""
        try:
            # Check if ML is available
            if not self.ml_enabled or not SKLEARN_AVAILABLE:
                logger.warning("ML features not available, using basic similarity calculation")
                return self._calculate_basic_similarity_matrix(weather_profiles)

            df = self.prepare_weather_data(weather_profiles)
            if df.empty:
                return np.array([])

            # Select features for similarity calculation
            feature_columns = [
                "temperature",
                "humidity",
                "wind_speed",
                "pressure",
                "uv_index",
                "visibility",
            ]
            features = df[feature_columns].values

            # Error boundary for sklearn operations
            try:
                # Normalize features
                features_scaled = self.scaler.fit_transform(features)
                # Calculate cosine similarity
                similarity_matrix = cosine_similarity(features_scaled)
            except Exception as sklearn_error:
                logger.error(f"Sklearn operation failed: {sklearn_error}, falling back to basic calculation")
                return self._calculate_basic_similarity_matrix(weather_profiles)

            logger.info(f"Calculated similarity matrix for {len(df)} cities")
            return similarity_matrix

        except Exception as e:
            logger.error(f"Error calculating similarity matrix: {e}")
            return np.array([])

    def _calculate_basic_similarity_matrix(self, weather_profiles: List[WeatherProfile]) -> np.ndarray:
        """Fallback similarity calculation without sklearn."""
        try:
            df = self.prepare_weather_data(weather_profiles)
            if df.empty:
                return np.array([])

            feature_columns = ["temperature", "humidity", "wind_speed", "pressure"]
            features = df[feature_columns].values
            n_cities = len(features)
            
            # Simple normalized euclidean distance converted to similarity
            similarity_matrix = np.zeros((n_cities, n_cities))
            
            for i in range(n_cities):
                for j in range(n_cities):
                    if i == j:
                        similarity_matrix[i][j] = 1.0
                    else:
                        # Calculate normalized distance
                        diff = np.abs(features[i] - features[j])
                        # Normalize by feature ranges (rough approximation)
                        normalized_diff = diff / np.array([50, 100, 20, 100])  # temp, humidity, wind, pressure ranges
                        distance = np.mean(normalized_diff)
                        similarity_matrix[i][j] = max(0, 1 - distance)
            
            logger.info(f"Calculated basic similarity matrix for {n_cities} cities")
            return similarity_matrix
            
        except Exception as e:
            logger.error(f"Error in basic similarity calculation: {e}")
            return np.array([])

    def get_city_similarity(
        self, city1: str, city2: str, weather_profiles: List[WeatherProfile]
    ) -> SimilarityResult:
        """Get detailed similarity analysis between two cities."""
        try:
            df = self.prepare_weather_data(weather_profiles)
            similarity_matrix = self.calculate_similarity_matrix(weather_profiles)

            if df.empty or similarity_matrix.size == 0:
                return SimilarityResult(city1, city2, 0.0, [], "Unable to calculate similarity")

            # Find city indices
            city1_idx = df[df["city_name"] == city1].index
            city2_idx = df[df["city_name"] == city2].index

            if len(city1_idx) == 0 or len(city2_idx) == 0:
                return SimilarityResult(city1, city2, 0.0, [], "Cities not found in data")

            city1_idx, city2_idx = city1_idx[0], city2_idx[0]
            similarity_score = similarity_matrix[city1_idx][city2_idx]

            # Analyze dominant factors
            city1_data = df.iloc[city1_idx]
            city2_data = df.iloc[city2_idx]

            feature_diffs = {
                "temperature": abs(city1_data["temperature"] - city2_data["temperature"]),
                "humidity": abs(city1_data["humidity"] - city2_data["humidity"]),
                "wind_speed": abs(city1_data["wind_speed"] - city2_data["wind_speed"]),
                "pressure": abs(city1_data["pressure"] - city2_data["pressure"]),
            }

            # Find most similar factors (smallest differences)
            sorted_factors = sorted(feature_diffs.items(), key=lambda x: x[1])
            dominant_factors = [factor[0] for factor in sorted_factors[:2]]

            # Generate recommendation
            similarity_percentage = similarity_score * 100
            if similarity_percentage >= 85:
                recommendation = f"{city1} and {city2} have very similar weather patterns - excellent for consistent experiences!"
            elif similarity_percentage >= 70:
                recommendation = f"{city1} and {city2} have similar weather with minor variations - good compatibility."
            elif similarity_percentage >= 50:
                recommendation = f"{city1} and {city2} have moderate weather differences - some adaptation needed."
            else:
                recommendation = f"{city1} and {city2} have quite different weather patterns - significant variation expected."

            return SimilarityResult(
                city1=city1,
                city2=city2,
                similarity_score=similarity_score,
                dominant_factors=dominant_factors,
                recommendation=recommendation,
            )

        except Exception as e:
            logger.error(f"Error calculating city similarity: {e}")
            return SimilarityResult(city1, city2, 0.0, [], f"Error: {str(e)}")

    def perform_weather_clustering(
        self, weather_profiles: List[WeatherProfile]
    ) -> List[ClusterResult]:
        """Perform K-means clustering on weather data with error boundaries."""
        try:
            # Check if ML is available
            if not self.ml_enabled or not SKLEARN_AVAILABLE:
                logger.warning("ML clustering not available, using basic grouping")
                return self._perform_basic_clustering(weather_profiles)

            df = self.prepare_weather_data(weather_profiles)
            if df.empty:
                return []

            # Select features for clustering
            feature_columns = ["temperature", "humidity", "wind_speed", "pressure", "uv_index"]
            features = df[feature_columns].values

            # Error boundary for sklearn clustering operations
            try:
                # Normalize features
                features_scaled = self.scaler.fit_transform(features)

                # Apply PCA for dimensionality reduction if needed
                if len(feature_columns) > 3:
                    # Dynamically set PCA components based on data size
                    n_components = min(3, len(df), len(feature_columns))
                    self.pca = PCA(n_components=n_components)
                    features_pca = self.pca.fit_transform(features_scaled)
                else:
                    features_pca = features_scaled

                # Perform clustering
                n_clusters = min(5, len(df))  # Adjust clusters based on data size
                self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                cluster_labels = self.kmeans.fit_predict(features_pca)
                
            except Exception as sklearn_error:
                logger.error(f"Sklearn clustering failed: {sklearn_error}, falling back to basic clustering")
                return self._perform_basic_clustering(weather_profiles)

            # Analyze clusters
            df["cluster"] = cluster_labels
            cluster_results = []

            for cluster_id in range(n_clusters):
                cluster_cities = df[df["cluster"] == cluster_id]["city_name"].tolist()
                cluster_data = df[df["cluster"] == cluster_id][feature_columns]

                # Calculate cluster characteristics
                characteristics = {
                    "avg_temperature": float(cluster_data["temperature"].mean()),
                    "avg_humidity": float(cluster_data["humidity"].mean()),
                    "avg_wind_speed": float(cluster_data["wind_speed"].mean()),
                    "avg_pressure": float(cluster_data["pressure"].mean()),
                }

                # Get cluster profile or create default
                profile = self.cluster_profiles.get(
                    cluster_id,
                    {
                        "name": f"Cluster {cluster_id}",
                        "emoji": "🌤️",
                        "desc": "Mixed weather conditions",
                    },
                )

                cluster_results.append(
                    ClusterResult(
                        cluster_id=cluster_id,
                        cluster_name=profile["name"],
                        cities=cluster_cities,
                        characteristics=characteristics,
                        emoji=profile["emoji"],
                        description=profile["desc"],
                    )
                )

            logger.info(f"Performed clustering analysis with {n_clusters} clusters")
            return cluster_results

        except Exception as e:
            logger.error(f"Error performing weather clustering: {e}")
            return []

    def _perform_basic_clustering(self, weather_profiles: List[WeatherProfile]) -> List[ClusterResult]:
        """Fallback clustering using simple temperature-based grouping."""
        try:
            df = self.prepare_weather_data(weather_profiles)
            if df.empty:
                return []

            # Simple temperature-based clustering
            def get_temp_cluster(temp):
                if temp < 10:
                    return 3  # Cool & Crisp
                elif temp < 20:
                    return 0  # Mild & Cloudy
                elif temp < 30:
                    return 4  # Tropical
                else:
                    return 1  # Dry Heat

            df["cluster"] = df["temperature"].apply(get_temp_cluster)
            cluster_results = []

            for cluster_id in df["cluster"].unique():
                cluster_cities = df[df["cluster"] == cluster_id]["city_name"].tolist()
                cluster_data = df[df["cluster"] == cluster_id]

                # Calculate cluster characteristics
                characteristics = {
                    "avg_temperature": float(cluster_data["temperature"].mean()),
                    "avg_humidity": float(cluster_data["humidity"].mean()),
                    "avg_wind_speed": float(cluster_data["wind_speed"].mean()),
                    "avg_pressure": float(cluster_data["pressure"].mean()),
                }

                # Get cluster profile
                profile = self.cluster_profiles.get(
                    cluster_id,
                    {
                        "name": f"Group {cluster_id}",
                        "emoji": "🌤️",
                        "desc": "Basic weather grouping",
                    },
                )

                cluster_results.append(
                    ClusterResult(
                        cluster_id=cluster_id,
                        cluster_name=profile["name"],
                        cities=cluster_cities,
                        characteristics=characteristics,
                        emoji=profile["emoji"],
                        description=profile["desc"],
                    )
                )

            logger.info(f"Performed basic clustering with {len(cluster_results)} groups")
            return cluster_results

        except Exception as e:
            logger.error(f"Error in basic clustering: {e}")
            return []

    def recommend_city_by_preferences(
        self, preferences: Dict[str, Any], weather_profiles: List[WeatherProfile]
    ) -> Optional[RecommendationResult]:
        """Recommend a city based on user weather preferences with error boundaries."""
        try:
            # Check if ML is available
            if not self.ml_enabled or not SKLEARN_AVAILABLE:
                logger.warning("ML recommendations not available, using basic matching")
                return self._recommend_city_basic(preferences, weather_profiles)

            df = self.prepare_weather_data(weather_profiles)
            if df.empty:
                return None

            # Create preference vector
            pref_vector = np.array(
                [
                    preferences.get("temperature", 20),
                    preferences.get("humidity", 50),
                    preferences.get("wind_speed", 5),
                    preferences.get("pressure", 1013),
                    preferences.get("uv_index", 5),
                    preferences.get("visibility", 10),
                ]
            ).reshape(1, -1)

            # Error boundary for sklearn operations
            try:
                # Normalize preference vector
                feature_columns = [
                    "temperature",
                    "humidity",
                    "wind_speed",
                    "pressure",
                    "uv_index",
                    "visibility",
                ]
                features = df[feature_columns].values
                features_scaled = self.scaler.fit_transform(features)
                pref_scaled = self.scaler.transform(pref_vector)

                # Find nearest neighbors
                self.nn_model.fit(features_scaled)
                distances, indices = self.nn_model.kneighbors(pref_scaled)

                # Get best match
                best_match_idx = indices[0][0]
                best_match_distance = distances[0][0]

                recommended_city = df.iloc[best_match_idx]["city_name"]
                match_percentage = max(0, (1 - best_match_distance) * 100)
                
            except Exception as sklearn_error:
                logger.error(f"Sklearn recommendation failed: {sklearn_error}, falling back to basic matching")
                return self._recommend_city_basic(preferences, weather_profiles)

            # Generate reasons
            city_data = df.iloc[best_match_idx]
            reasons = []

            temp_diff = abs(city_data["temperature"] - preferences.get("temperature", 20))
            if temp_diff < 5:
                reasons.append(
                    f"Temperature matches your preference ({city_data['temperature']:.1f}°C)"
                )

            humidity_diff = abs(city_data["humidity"] - preferences.get("humidity", 50))
            if humidity_diff < 15:
                reasons.append(f"Humidity level is ideal ({city_data['humidity']:.1f}%)")

            wind_diff = abs(city_data["wind_speed"] - preferences.get("wind_speed", 5))
            if wind_diff < 3:
                reasons.append(f"Wind conditions are suitable ({city_data['wind_speed']:.1f} m/s)")

            # Get cluster information
            clusters = self.perform_weather_clustering(weather_profiles)
            cluster_info = None
            for cluster in clusters:
                if recommended_city in cluster.cities:
                    cluster_info = cluster
                    break

            if not cluster_info:
                cluster_info = ClusterResult(
                    cluster_id=0,
                    cluster_name="General",
                    cities=[recommended_city],
                    characteristics={},
                    emoji="🌤️",
                    description="Standard weather conditions",
                )

            # Comparison data
            comparison_data = {
                "your_preferences": preferences,
                "recommended_city_data": {
                    "temperature": float(city_data["temperature"]),
                    "humidity": float(city_data["humidity"]),
                    "wind_speed": float(city_data["wind_speed"]),
                    "pressure": float(city_data["pressure"]),
                },
                "differences": {
                    "temperature": float(temp_diff),
                    "humidity": float(humidity_diff),
                    "wind_speed": float(wind_diff),
                },
            }

            return RecommendationResult(
                recommended_city=recommended_city,
                match_percentage=match_percentage,
                reasons=reasons,
                cluster_info=cluster_info,
                comparison_data=comparison_data,
            )

        except Exception as e:
            logger.error(f"Error generating city recommendation: {e}")
            return None

    def _recommend_city_basic(
        self, preferences: Dict[str, Any], weather_profiles: List[WeatherProfile]
    ) -> Optional[RecommendationResult]:
        """Fallback city recommendation using simple distance calculation."""
        try:
            df = self.prepare_weather_data(weather_profiles)
            if df.empty:
                return None

            # Simple distance-based matching
            best_city = None
            best_score = float('inf')
            best_idx = 0

            pref_temp = preferences.get("temperature", 20)
            pref_humidity = preferences.get("humidity", 50)
            pref_wind = preferences.get("wind_speed", 5)
            pref_pressure = preferences.get("pressure", 1013)

            for idx, row in df.iterrows():
                # Calculate weighted distance
                temp_diff = abs(row["temperature"] - pref_temp) / 50  # normalize by typical range
                humidity_diff = abs(row["humidity"] - pref_humidity) / 100
                wind_diff = abs(row["wind_speed"] - pref_wind) / 20
                pressure_diff = abs(row["pressure"] - pref_pressure) / 100

                # Weighted score
                score = (
                    temp_diff * 0.4 +
                    humidity_diff * 0.3 +
                    wind_diff * 0.2 +
                    pressure_diff * 0.1
                )

                if score < best_score:
                    best_score = score
                    best_city = row["city_name"]
                    best_idx = idx

            if best_city is None:
                return None

            # Calculate match percentage
            match_percentage = max(0, (1 - best_score) * 100)

            # Generate reasons
            city_data = df.iloc[best_idx]
            reasons = []

            temp_diff = abs(city_data["temperature"] - pref_temp)
            if temp_diff < 5:
                reasons.append(f"Temperature close to preference ({city_data['temperature']:.1f}°C)")

            humidity_diff = abs(city_data["humidity"] - pref_humidity)
            if humidity_diff < 15:
                reasons.append(f"Humidity level suitable ({city_data['humidity']:.1f}%)")

            if not reasons:
                reasons.append("Best available match from current data")

            # Create basic cluster info
            cluster_info = ClusterResult(
                cluster_id=0,
                cluster_name="Basic Match",
                cities=[best_city],
                characteristics={},
                emoji="🌤️",
                description="Simple preference matching",
            )

            # Comparison data
            comparison_data = {
                "your_preferences": preferences,
                "recommended_city_data": {
                    "temperature": float(city_data["temperature"]),
                    "humidity": float(city_data["humidity"]),
                    "wind_speed": float(city_data["wind_speed"]),
                    "pressure": float(city_data["pressure"]),
                },
                "differences": {
                    "temperature": float(temp_diff),
                    "humidity": float(humidity_diff),
                    "wind_speed": float(abs(city_data["wind_speed"] - pref_wind)),
                },
            }

            return RecommendationResult(
                recommended_city=best_city,
                match_percentage=match_percentage,
                reasons=reasons,
                cluster_info=cluster_info,
                comparison_data=comparison_data,
            )

        except Exception as e:
            logger.error(f"Error in basic city recommendation: {e}")
            return None

    def create_similarity_heatmap(
        self, weather_profiles: List[WeatherProfile], figsize=(10, 8), theme=None
    ) -> plt.Figure:
        """Create a similarity heatmap visualization with theme support."""
        try:
            df = self.prepare_weather_data(weather_profiles)
            similarity_matrix = self.calculate_similarity_matrix(weather_profiles)

            # Apply theme settings
            self._apply_chart_theme(theme)

            if df.empty or similarity_matrix.size == 0:
                fig, ax = plt.subplots(figsize=figsize)
                ax.text(
                    0.5,
                    0.5,
                    "No data available",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
                )
                self._style_figure(fig, ax, theme)
                return fig

            # Create heatmap
            fig, ax = plt.subplots(figsize=figsize)

            city_names = df["city_name"].tolist()

            # Create custom colormap based on theme
            if theme:
                primary_color = theme.get("primary", "#00FF41")
                secondary_color = theme.get("secondary", "#008F11")
                # Create a custom colormap using theme colors
                from matplotlib.colors import LinearSegmentedColormap

                colors = ["#000000", secondary_color, primary_color]
                n_bins = 100
                cmap = LinearSegmentedColormap.from_list("theme_cmap", colors, N=n_bins)
            else:
                cmap = "RdYlBu_r"

            # Create heatmap with seaborn
            sns.heatmap(
                similarity_matrix,
                annot=True,
                fmt=".2f",
                cmap=cmap,
                xticklabels=city_names,
                yticklabels=city_names,
                ax=ax,
                cbar_kws={"label": "Similarity Score"},
                annot_kws={"color": theme.get("text", "#E0E0E0") if theme else "#E0E0E0"},
            )

            self._style_figure(fig, ax, theme)
            ax.set_title(
                "🔥 City Weather Similarity Heatmap",
                fontsize=16,
                fontweight="bold",
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            ax.set_xlabel(
                "Cities", fontsize=12, color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0"
            )
            ax.set_ylabel(
                "Cities", fontsize=12, color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0"
            )

            plt.xticks(rotation=45, ha="right")
            plt.yticks(rotation=0)
            plt.tight_layout()

            logger.info("Created similarity heatmap")
            return fig

        except Exception as e:
            logger.error(f"Error creating similarity heatmap: {e}")
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(
                0.5,
                0.5,
                f"Error: {str(e)}",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            self._style_figure(fig, ax, theme)
            return fig

    def create_cluster_visualization(
        self, weather_profiles: List[WeatherProfile], figsize=(12, 8), theme=None
    ) -> plt.Figure:
        """Create cluster visualization with PCA and theme support."""
        try:
            # Apply theme settings
            self._apply_chart_theme(theme)

            df = self.prepare_weather_data(weather_profiles)
            if df.empty:
                fig, ax = plt.subplots(figsize=figsize)
                ax.text(
                    0.5,
                    0.5,
                    "No data available",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
                )
                self._style_figure(fig, ax, theme)
                return fig

            # Perform clustering
            clusters = self.perform_weather_clustering(weather_profiles)

            # Check if ML features are available
            if not self.ml_enabled or not SKLEARN_AVAILABLE:
                return self._create_basic_cluster_visualization(weather_profiles, figsize, theme)

            try:
                # Prepare features for PCA visualization
                feature_columns = ["temperature", "humidity", "wind_speed", "pressure", "uv_index"]
                features = df[feature_columns].values
                features_scaled = self.scaler.fit_transform(features)

                # Apply PCA for 2D visualization
                pca_2d = PCA(n_components=2)
                features_2d = pca_2d.fit_transform(features_scaled)
            except Exception as e:
                logger.warning(f"PCA visualization failed, using basic visualization: {e}")
                return self._create_basic_cluster_visualization(weather_profiles, figsize, theme)

            # Create visualization
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

            # Generate theme-based colors for clusters
            if theme:
                primary = theme.get("primary", "#00FF41")
                secondary = theme.get("secondary", "#008F11")
                accent = theme.get("accent", "#FF6B35")
                chart_colors = theme.get(
                    "chart_colors", [primary, secondary, accent, "#FFD700", "#FF69B4", "#00CED1"]
                )
                colors = (
                    chart_colors[: len(clusters)]
                    if len(clusters) <= len(chart_colors)
                    else plt.cm.Set3(np.linspace(0, 1, len(clusters)))
                )
            else:
                colors = plt.cm.Set3(np.linspace(0, 1, len(clusters)))

            # Cluster scatter plot
            for i, cluster in enumerate(clusters):
                cluster_indices = df[df["city_name"].isin(cluster.cities)].index
                if len(cluster_indices) > 0:
                    color = colors[i] if isinstance(colors, list) else colors[i]
                    ax1.scatter(
                        features_2d[cluster_indices, 0],
                        features_2d[cluster_indices, 1],
                        c=[color],
                        label=f"{cluster.emoji} {cluster.cluster_name}",
                        s=100,
                        alpha=0.8,
                        edgecolors=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
                        linewidth=1,
                    )

                    # Add city labels
                    for idx in cluster_indices:
                        ax1.annotate(
                            df.iloc[idx]["city_name"],
                            (features_2d[idx, 0], features_2d[idx, 1]),
                            xytext=(5, 5),
                            textcoords="offset points",
                            fontsize=8,
                            alpha=0.9,
                            color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
                            weight="bold",
                        )

            self._style_figure(fig, ax1, theme)
            ax1.set_title(
                "🌍 Weather Clusters (PCA Visualization)",
                fontsize=14,
                fontweight="bold",
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            ax1.set_xlabel(
                f"PC1 ({pca_2d.explained_variance_ratio_[0]:.1%} variance)",
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            ax1.set_ylabel(
                f"PC2 ({pca_2d.explained_variance_ratio_[1]:.1%} variance)",
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            ax1.legend(
                bbox_to_anchor=(1.05, 1),
                loc="upper left",
                facecolor=theme.get("card_bg", "#1E1E1E") if theme else "#1E1E1E",
                edgecolor=theme.get("primary", "#00FF41") if theme else "#00FF41",
                labelcolor=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            ax1.grid(True, alpha=0.3, color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0")

            # Cluster characteristics bar chart
            cluster_names = [f"{c.emoji} {c.cluster_name}" for c in clusters]
            avg_temps = [c.characteristics.get("avg_temperature", 0) for c in clusters]

            # Use theme colors for bars
            bar_colors = (
                colors[: len(clusters)]
                if isinstance(colors, list)
                else [colors[i] for i in range(len(clusters))]
            )
            bars = ax2.bar(
                range(len(cluster_names)),
                avg_temps,
                color=bar_colors,
                alpha=0.8,
                edgecolor=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
                linewidth=1,
            )

            self._style_figure(fig, ax2, theme)
            ax2.set_title(
                "📊 Average Temperature by Cluster",
                fontsize=14,
                fontweight="bold",
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            ax2.set_xlabel(
                "Weather Clusters", color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0"
            )
            ax2.set_ylabel(
                "Average Temperature (°C)",
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            ax2.set_xticks(range(len(cluster_names)))
            ax2.set_xticklabels(
                cluster_names,
                rotation=45,
                ha="right",
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            ax2.grid(True, alpha=0.3, color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0")

            # Add value labels on bars
            for bar, temp in zip(bars, avg_temps):
                ax2.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.5,
                    f"{temp:.1f}°C",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
                    weight="bold",
                )

            plt.tight_layout()

            logger.info("Created cluster visualization")
            return fig

        except Exception as e:
            logger.error(f"Error creating cluster visualization: {e}")
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(
                0.5,
                0.5,
                f"Error: {str(e)}",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            self._style_figure(fig, ax, theme)
            return fig

    def _create_basic_cluster_visualization(
        self, weather_profiles: List[WeatherProfile], figsize=(12, 8), theme=None
    ) -> plt.Figure:
        """Fallback cluster visualization without PCA."""
        try:
            # Apply theme settings
            self._apply_chart_theme(theme)

            df = self.prepare_weather_data(weather_profiles)
            if df.empty:
                fig, ax = plt.subplots(figsize=figsize)
                ax.text(
                    0.5,
                    0.5,
                    "No data available",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
                )
                self._style_figure(fig, ax, theme)
                return fig

            # Perform basic clustering
            clusters = self.perform_weather_clustering(weather_profiles)

            # Create simple temperature vs humidity scatter plot
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

            # Generate theme-based colors for clusters
            if theme:
                primary = theme.get("primary", "#00FF41")
                secondary = theme.get("secondary", "#008F11")
                accent = theme.get("accent", "#FF6B35")
                chart_colors = theme.get(
                    "chart_colors", [primary, secondary, accent, "#FFD700", "#FF69B4", "#00CED1"]
                )
                colors = (
                    chart_colors[: len(clusters)]
                    if len(clusters) <= len(chart_colors)
                    else plt.cm.Set3(np.linspace(0, 1, len(clusters)))
                )
            else:
                colors = plt.cm.Set3(np.linspace(0, 1, len(clusters)))

            # Simple scatter plot using temperature and humidity
            for i, cluster in enumerate(clusters):
                cluster_indices = df[df["city_name"].isin(cluster.cities)].index
                if len(cluster_indices) > 0:
                    color = colors[i] if isinstance(colors, list) else colors[i]
                    cluster_data = df.iloc[cluster_indices]
                    
                    ax1.scatter(
                        cluster_data["temperature"],
                        cluster_data["humidity"],
                        c=[color],
                        label=f"{cluster.emoji} {cluster.cluster_name}",
                        s=100,
                        alpha=0.8,
                        edgecolors=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
                        linewidth=1,
                    )

                    # Add city labels
                    for idx in cluster_indices:
                        ax1.annotate(
                            df.iloc[idx]["city_name"],
                            (df.iloc[idx]["temperature"], df.iloc[idx]["humidity"]),
                            xytext=(5, 5),
                            textcoords="offset points",
                            fontsize=8,
                            alpha=0.9,
                            color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
                            weight="bold",
                        )

            self._style_figure(fig, ax1, theme)
            ax1.set_title(
                "🌍 Weather Clusters (Temperature vs Humidity)",
                fontsize=14,
                fontweight="bold",
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            ax1.set_xlabel(
                "Temperature (°C)",
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            ax1.set_ylabel(
                "Humidity (%)",
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            ax1.legend(
                bbox_to_anchor=(1.05, 1),
                loc="upper left",
                facecolor=theme.get("card_bg", "#1E1E1E") if theme else "#1E1E1E",
                edgecolor=theme.get("primary", "#00FF41") if theme else "#00FF41",
                labelcolor=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            ax1.grid(True, alpha=0.3, color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0")

            # Cluster characteristics bar chart
            cluster_names = [f"{c.emoji} {c.cluster_name}" for c in clusters]
            avg_temps = [c.characteristics.get("avg_temperature", 0) for c in clusters]

            # Use theme colors for bars
            bar_colors = (
                colors[: len(clusters)]
                if isinstance(colors, list)
                else [colors[i] for i in range(len(clusters))]
            )
            bars = ax2.bar(
                range(len(cluster_names)),
                avg_temps,
                color=bar_colors,
                alpha=0.8,
                edgecolor=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
                linewidth=1,
            )

            # Add value labels on bars
            for bar, temp in zip(bars, avg_temps):
                height = bar.get_height()
                ax2.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.5,
                    f"{temp:.1f}°C",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
                    weight="bold",
                )

            self._style_figure(fig, ax2, theme)
            ax2.set_title(
                "📊 Average Temperature by Cluster",
                fontsize=14,
                fontweight="bold",
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            ax2.set_xlabel(
                "Clusters", color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0"
            )
            ax2.set_ylabel(
                "Temperature (°C)", color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0"
            )
            ax2.set_xticks(range(len(cluster_names)))
            ax2.set_xticklabels(cluster_names, rotation=45, ha="right")
            ax2.grid(True, alpha=0.3, color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0")

            plt.tight_layout()
            logger.info("Created basic cluster visualization")
            return fig

        except Exception as e:
            logger.error(f"Error creating basic cluster visualization: {e}")
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(
                0.5,
                0.5,
                f"Error: {str(e)}",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            self._style_figure(fig, ax, theme)
            return fig

    def create_radar_chart(
        self,
        weather_profiles: List[WeatherProfile],
        selected_cities: List[str] = None,
        figsize=(10, 10),
        theme=None,
    ) -> plt.Figure:
        """Create radar chart for weather comparison with theme support."""
        try:
            # Apply theme settings
            self._apply_chart_theme(theme)

            df = self.prepare_weather_data(weather_profiles)
            if df.empty:
                fig, ax = plt.subplots(figsize=figsize)
                ax.text(
                    0.5,
                    0.5,
                    "No data available",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
                )
                self._style_figure(fig, ax, theme)
                return fig

            # Filter for selected cities if provided
            if selected_cities:
                df = df[df["city_name"].isin(selected_cities)]

            if df.empty:
                fig, ax = plt.subplots(figsize=figsize)
                ax.text(
                    0.5,
                    0.5,
                    "No cities selected",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
                )
                self._style_figure(fig, ax, theme)
                return fig

            # Prepare radar chart data
            categories = [
                "🌡️ Temperature",
                "💧 Humidity",
                "💨 Wind Speed",
                "🌊 Pressure",
                "☀️ UV Index",
            ]

            # Normalize data to 0-100 scale for radar chart
            normalized_data = df.copy()
            normalized_data["temperature"] = (
                (df["temperature"] + 20) / 60 * 100
            )  # -20 to 40°C -> 0-100
            normalized_data["humidity"] = df["humidity"]  # Already 0-100
            normalized_data["wind_speed"] = df["wind_speed"] / 20 * 100  # 0-20 m/s -> 0-100
            normalized_data["pressure"] = (
                (df["pressure"] - 950) / 100 * 100
            )  # 950-1050 hPa -> 0-100
            normalized_data["uv_index"] = df["uv_index"] / 12 * 100  # 0-12 -> 0-100

            # Create radar chart
            fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(projection="polar"))

            # Calculate angles for each category
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            angles += angles[:1]  # Complete the circle

            # Generate theme-based colors for cities
            if theme:
                primary = theme.get("primary", "#00FF41")
                secondary = theme.get("secondary", "#008F11")
                accent = theme.get("accent", "#FF6B35")
                chart_colors = theme.get(
                    "chart_colors", [primary, secondary, accent, "#FFD700", "#FF69B4", "#00CED1"]
                )
                colors = (
                    chart_colors[: len(df)]
                    if len(df) <= len(chart_colors)
                    else plt.cm.Set3(np.linspace(0, 1, len(df)))
                )
            else:
                colors = plt.cm.Set3(np.linspace(0, 1, len(df)))

            # Plot each city
            for i, (_, city_data) in enumerate(df.iterrows()):
                values = [
                    normalized_data.iloc[i]["temperature"],
                    normalized_data.iloc[i]["humidity"],
                    normalized_data.iloc[i]["wind_speed"],
                    normalized_data.iloc[i]["pressure"],
                    normalized_data.iloc[i]["uv_index"],
                ]
                values += values[:1]  # Complete the circle

                color = colors[i] if isinstance(colors, list) else colors[i]
                ax.plot(
                    angles,
                    values,
                    "o-",
                    linewidth=3,
                    label=city_data["city_name"],
                    color=color,
                    markersize=8,
                )
                ax.fill(angles, values, alpha=0.15, color=color)

            # Apply theme styling to polar chart
            self._style_polar_chart(ax, theme)

            # Customize the chart
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(
                categories, color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0", fontsize=11
            )
            ax.set_ylim(0, 100)
            ax.set_yticks([20, 40, 60, 80, 100])
            ax.set_yticklabels(
                ["20%", "40%", "60%", "80%", "100%"],
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
                fontsize=9,
            )
            ax.grid(True, alpha=0.3, color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0")

            plt.title(
                "🎯 Weather Profile Comparison\n(Radar Chart)",
                size=16,
                fontweight="bold",
                pad=20,
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            plt.legend(
                loc="upper right",
                bbox_to_anchor=(1.3, 1.0),
                facecolor=theme.get("card_bg", "#1E1E1E") if theme else "#1E1E1E",
                edgecolor=theme.get("primary", "#00FF41") if theme else "#00FF41",
                labelcolor=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )

            logger.info("Created radar chart")
            return fig

        except Exception as e:
            logger.error(f"Error creating radar chart: {e}")
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(
                0.5,
                0.5,
                f"Error: {str(e)}",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color=theme.get("text", "#E0E0E0") if theme else "#E0E0E0",
            )
            self._style_figure(fig, ax, theme)
            return fig

    def _apply_chart_theme(self, theme):
        """Apply theme settings to matplotlib."""
        if theme:
            plt.rcParams.update(
                {
                    "figure.facecolor": theme.get("bg", "#000000"),
                    "axes.facecolor": theme.get("card_bg", "#1E1E1E"),
                    "axes.edgecolor": theme.get("primary", "#00FF41"),
                    "axes.labelcolor": theme.get("text", "#E0E0E0"),
                    "xtick.color": theme.get("text", "#E0E0E0"),
                    "ytick.color": theme.get("text", "#E0E0E0"),
                    "text.color": theme.get("text", "#E0E0E0"),
                    "axes.spines.left": True,
                    "axes.spines.bottom": True,
                    "axes.spines.top": False,
                    "axes.spines.right": False,
                    "axes.linewidth": 1.5,
                }
            )

    def _style_figure(self, fig, ax, theme):
        """Apply theme styling to a figure and axes."""
        if theme:
            fig.patch.set_facecolor(theme.get("bg", "#000000"))
            ax.set_facecolor(theme.get("card_bg", "#1E1E1E"))

            # Style spines
            for spine in ax.spines.values():
                spine.set_color(theme.get("primary", "#00FF41"))
                spine.set_linewidth(1.5)

            # Hide top and right spines
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            # Style ticks
            ax.tick_params(colors=theme.get("text", "#E0E0E0"), which="both")

    # ML Prediction Methods
    def load_or_train_models(self):
        """Load existing models or initialize for training."""
        if not SKLEARN_AVAILABLE:
            return
            
        try:
            # Try to load existing models
            temp_model_path = self.models_dir / "temperature_model.joblib"
            humid_model_path = self.models_dir / "humidity_model.joblib"
            temp_scaler_path = self.models_dir / "temperature_scaler.joblib"
            
            if temp_model_path.exists() and humid_model_path.exists() and temp_scaler_path.exists():
                self.prediction_models['temperature'] = joblib.load(temp_model_path)
                self.prediction_models['humidity'] = joblib.load(humid_model_path)
                self.prediction_scalers['temperature'] = joblib.load(temp_scaler_path)
                logger.info("Loaded existing ML prediction models")
            else:
                logger.info("No existing models found. Models will be trained when data is available.")
                
        except Exception as e:
            logger.error(f"Error loading ML models: {e}")
    
    def prepare_features(self, weather_data):
        """Extract features from weather data."""
        try:
            dt = datetime.fromtimestamp(weather_data.get('dt', datetime.now().timestamp()))
            
            features = {
                'temperature': weather_data.get('temp', 20),
                'humidity': weather_data.get('humidity', 50),
                'pressure': weather_data.get('pressure', 1013),
                'wind_speed': weather_data.get('wind_speed', 5),
                'hour': dt.hour,
                'day_of_week': dt.weekday(),
                'month': dt.month,
                'clouds': weather_data.get('clouds', 50),
                'visibility': weather_data.get('visibility', 10000) / 1000  # Convert to km
            }
            
            return np.array([features[name] for name in self.feature_names]).reshape(1, -1)
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return np.zeros((1, len(self.feature_names)))
    
    def train_models(self, historical_data):
        """Train ML models on historical data."""
        if not SKLEARN_AVAILABLE or len(historical_data) < 100:
            logger.warning("Insufficient data for training. Need at least 100 samples.")
            return False
        
        try:
            # Prepare training data
            X = []
            y_temp = []
            y_humid = []
            
            for i in range(len(historical_data) - 1):
                current = historical_data[i]
                next_hour = historical_data[i + 1]
                
                features = self.prepare_features(current)
                X.append(features[0])
                y_temp.append(next_hour['temp'])
                y_humid.append(next_hour['humidity'])
            
            X = np.array(X)
            y_temp = np.array(y_temp)
            y_humid = np.array(y_humid)
            
            # Train temperature model
            self.prediction_scalers['temperature'] = StandardScaler()
            X_scaled = self.prediction_scalers['temperature'].fit_transform(X)
            
            self.prediction_models['temperature'] = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
            self.prediction_models['temperature'].fit(X_scaled, y_temp)
            
            # Train humidity model
            self.prediction_models['humidity'] = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.prediction_models['humidity'].fit(X_scaled, y_humid)
            
            # Save models
            self.save_models()
            
            # Calculate and log accuracy
            self.evaluate_models(X_scaled, y_temp, y_humid)
            
            return True
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            return False
    
    def save_models(self):
        """Save trained models to disk."""
        try:
            if 'temperature' in self.prediction_models:
                joblib.dump(self.prediction_models['temperature'], self.models_dir / "temperature_model.joblib")
                joblib.dump(self.prediction_models['humidity'], self.models_dir / "humidity_model.joblib")
                joblib.dump(self.prediction_scalers['temperature'], self.models_dir / "temperature_scaler.joblib")
                logger.info("ML models saved successfully")
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def evaluate_models(self, X_scaled, y_temp, y_humid):
        """Evaluate model performance."""
        try:
            # Split data for evaluation
            X_train, X_test, y_temp_train, y_temp_test = train_test_split(
                X_scaled, y_temp, test_size=0.2, random_state=42
            )
            _, _, y_humid_train, y_humid_test = train_test_split(
                X_scaled, y_humid, test_size=0.2, random_state=42
            )
            
            # Evaluate temperature model
            temp_pred = self.prediction_models['temperature'].predict(X_test)
            temp_mae = mean_absolute_error(y_temp_test, temp_pred)
            temp_r2 = r2_score(y_temp_test, temp_pred)
            
            # Evaluate humidity model
            humid_pred = self.prediction_models['humidity'].predict(X_test)
            humid_mae = mean_absolute_error(y_humid_test, humid_pred)
            humid_r2 = r2_score(y_humid_test, humid_pred)
            
            logger.info(f"Temperature Model - MAE: {temp_mae:.2f}, R²: {temp_r2:.3f}")
            logger.info(f"Humidity Model - MAE: {humid_mae:.2f}, R²: {humid_r2:.3f}")
            
        except Exception as e:
            logger.error(f"Error evaluating models: {e}")
    
    def predict_weather(self, current_weather, hours_ahead=24):
        """Generate weather predictions."""
        if not SKLEARN_AVAILABLE:
            return self._fallback_predictions(current_weather, hours_ahead)
        
        predictions = []
        current_data = current_weather.copy()
        
        try:
            for hour in range(hours_ahead):
                features = self.prepare_features(current_data)
                
                if 'temperature' in self.prediction_models and 'temperature' in self.prediction_scalers:
                    features_scaled = self.prediction_scalers['temperature'].transform(features)
                    
                    # Predict
                    temp_pred = self.prediction_models['temperature'].predict(features_scaled)[0]
                    humid_pred = self.prediction_models['humidity'].predict(features_scaled)[0]
                    
                    # Add uncertainty bounds
                    temp_std = self.calculate_prediction_uncertainty(features_scaled, 'temperature')
                    humid_std = self.calculate_prediction_uncertainty(features_scaled, 'humidity')
                    
                    prediction = {
                        'hour': hour + 1,
                        'temperature': round(temp_pred, 1),
                        'temperature_min': round(temp_pred - temp_std, 1),
                        'temperature_max': round(temp_pred + temp_std, 1),
                        'humidity': round(humid_pred, 0),
                        'humidity_min': round(max(0, humid_pred - humid_std), 0),
                        'humidity_max': round(min(100, humid_pred + humid_std), 0),
                        'confidence': self.calculate_confidence(hour)
                    }
                    
                    predictions.append(prediction)
                    
                    # Update current_data for next prediction
                    current_data['temp'] = temp_pred
                    current_data['humidity'] = humid_pred
                    current_data['dt'] += 3600  # Add 1 hour
                else:
                    # Fallback to simple prediction
                    predictions.append(self.simple_prediction(current_data, hour + 1))
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error in weather prediction: {e}")
            return self._fallback_predictions(current_weather, hours_ahead)
    
    def calculate_prediction_uncertainty(self, features, model_type):
        """Calculate prediction uncertainty using ensemble variance."""
        try:
            if model_type == 'temperature':
                # For gradient boosting, use staged predictions
                predictions = []
                for pred in self.prediction_models[model_type].staged_predict(features):
                    predictions.append(pred[0])
                return np.std(predictions[-10:])  # Use last 10 estimators
            else:
                # For random forest, use tree predictions
                predictions = []
                for tree in self.prediction_models[model_type].estimators_:
                    predictions.append(tree.predict(features)[0])
                return np.std(predictions)
        except Exception as e:
            logger.error(f"Error calculating uncertainty: {e}")
            return 2.0  # Default uncertainty
    
    def calculate_confidence(self, hours_ahead):
        """Calculate prediction confidence based on time horizon."""
        # Confidence decreases with prediction horizon
        base_confidence = 0.95
        decay_rate = 0.02
        return max(0.5, base_confidence - (decay_rate * hours_ahead))
    
    def simple_prediction(self, current_data, hour):
        """Simple fallback prediction when ML models are not available."""
        # Simple linear trend with some randomness
        temp_change = np.random.normal(0, 1)  # Random temperature change
        humid_change = np.random.normal(0, 5)  # Random humidity change
        
        return {
            'hour': hour,
            'temperature': round(current_data.get('temp', 20) + temp_change, 1),
            'temperature_min': round(current_data.get('temp', 20) + temp_change - 2, 1),
            'temperature_max': round(current_data.get('temp', 20) + temp_change + 2, 1),
            'humidity': round(max(0, min(100, current_data.get('humidity', 50) + humid_change)), 0),
            'humidity_min': round(max(0, current_data.get('humidity', 50) + humid_change - 10), 0),
            'humidity_max': round(min(100, current_data.get('humidity', 50) + humid_change + 10), 0),
            'confidence': max(0.3, 0.8 - (0.02 * hour))
        }
    
    def _fallback_predictions(self, current_weather, hours_ahead):
        """Fallback predictions when ML is not available."""
        predictions = []
        for hour in range(hours_ahead):
            predictions.append(self.simple_prediction(current_weather, hour + 1))
        return predictions

    def _style_polar_chart(self, ax, theme):
        """Apply theme styling to a polar chart."""
        if theme:
            ax.set_facecolor(theme.get("card_bg", "#1E1E1E"))
            ax.figure.patch.set_facecolor(theme.get("bg", "#000000"))

            # Style radial grid lines
            ax.tick_params(colors=theme.get("text", "#E0E0E0"))

            # Style the polar plot border
            ax.spines["polar"].set_color(theme.get("primary", "#00FF41"))
            ax.spines["polar"].set_linewidth(2)
