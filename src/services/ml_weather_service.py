"""Machine Learning Weather Service for advanced analytics and recommendations."""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

# ML Libraries
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches

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
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=3)
        self.kmeans = KMeans(n_clusters=5, random_state=42)
        self.nn_model = NearestNeighbors(n_neighbors=5, metric='cosine')
        
        # Weather feature weights for different analysis types
        self.similarity_weights = {
            'temperature': 0.3,
            'humidity': 0.2,
            'wind_speed': 0.2,
            'pressure': 0.15,
            'uv_index': 0.1,
            'visibility': 0.05
        }
        
        # Cluster characteristics
        self.cluster_profiles = {
            0: {'name': 'Mild & Cloudy', 'emoji': '☁️', 'desc': 'Comfortable temperatures with moderate humidity'},
            1: {'name': 'Dry Heat', 'emoji': '🔥', 'desc': 'High temperatures with low humidity'},
            2: {'name': 'Storm Watch', 'emoji': '🌧️', 'desc': 'High humidity with variable conditions'},
            3: {'name': 'Cool & Crisp', 'emoji': '❄️', 'desc': 'Low temperatures with clear conditions'},
            4: {'name': 'Tropical', 'emoji': '🌴', 'desc': 'Warm and humid conditions'}
        }
        
        logger.info("ML Weather Service initialized")
    
    def prepare_weather_data(self, weather_profiles: List[WeatherProfile]) -> pd.DataFrame:
        """Prepare weather data for ML analysis."""
        try:
            data = []
            for profile in weather_profiles:
                data.append({
                    'city_name': profile.city_name,
                    'temperature': profile.temperature,
                    'humidity': profile.humidity,
                    'wind_speed': profile.wind_speed,
                    'pressure': profile.pressure,
                    'uv_index': profile.uv_index,
                    'visibility': profile.visibility,
                    'feels_like': profile.feels_like or profile.temperature,
                    'is_team_member': profile.is_team_member,
                    'member_name': profile.member_name
                })
            
            df = pd.DataFrame(data)
            
            # Handle missing values
            numeric_columns = ['temperature', 'humidity', 'wind_speed', 'pressure', 'uv_index', 'visibility', 'feels_like']
            df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].mean())
            
            logger.info(f"Prepared weather data for {len(df)} cities")
            return df
            
        except Exception as e:
            logger.error(f"Error preparing weather data: {e}")
            return pd.DataFrame()
    
    def calculate_similarity_matrix(self, weather_profiles: List[WeatherProfile]) -> np.ndarray:
        """Calculate similarity matrix between cities using cosine similarity."""
        try:
            df = self.prepare_weather_data(weather_profiles)
            if df.empty:
                return np.array([])
            
            # Select features for similarity calculation
            feature_columns = ['temperature', 'humidity', 'wind_speed', 'pressure', 'uv_index', 'visibility']
            features = df[feature_columns].values
            
            # Normalize features
            features_scaled = self.scaler.fit_transform(features)
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(features_scaled)
            
            logger.info(f"Calculated similarity matrix for {len(df)} cities")
            return similarity_matrix
            
        except Exception as e:
            logger.error(f"Error calculating similarity matrix: {e}")
            return np.array([])
    
    def get_city_similarity(self, city1: str, city2: str, weather_profiles: List[WeatherProfile]) -> SimilarityResult:
        """Get detailed similarity analysis between two cities."""
        try:
            df = self.prepare_weather_data(weather_profiles)
            similarity_matrix = self.calculate_similarity_matrix(weather_profiles)
            
            if df.empty or similarity_matrix.size == 0:
                return SimilarityResult(city1, city2, 0.0, [], "Unable to calculate similarity")
            
            # Find city indices
            city1_idx = df[df['city_name'] == city1].index
            city2_idx = df[df['city_name'] == city2].index
            
            if len(city1_idx) == 0 or len(city2_idx) == 0:
                return SimilarityResult(city1, city2, 0.0, [], "Cities not found in data")
            
            city1_idx, city2_idx = city1_idx[0], city2_idx[0]
            similarity_score = similarity_matrix[city1_idx][city2_idx]
            
            # Analyze dominant factors
            city1_data = df.iloc[city1_idx]
            city2_data = df.iloc[city2_idx]
            
            feature_diffs = {
                'temperature': abs(city1_data['temperature'] - city2_data['temperature']),
                'humidity': abs(city1_data['humidity'] - city2_data['humidity']),
                'wind_speed': abs(city1_data['wind_speed'] - city2_data['wind_speed']),
                'pressure': abs(city1_data['pressure'] - city2_data['pressure'])
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
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"Error calculating city similarity: {e}")
            return SimilarityResult(city1, city2, 0.0, [], f"Error: {str(e)}")
    
    def perform_weather_clustering(self, weather_profiles: List[WeatherProfile]) -> List[ClusterResult]:
        """Perform K-means clustering on weather data."""
        try:
            df = self.prepare_weather_data(weather_profiles)
            if df.empty:
                return []
            
            # Select features for clustering
            feature_columns = ['temperature', 'humidity', 'wind_speed', 'pressure', 'uv_index']
            features = df[feature_columns].values
            
            # Normalize features
            features_scaled = self.scaler.fit_transform(features)
            
            # Apply PCA for dimensionality reduction if needed
            if len(feature_columns) > 3:
                features_pca = self.pca.fit_transform(features_scaled)
            else:
                features_pca = features_scaled
            
            # Perform clustering
            n_clusters = min(5, len(df))  # Adjust clusters based on data size
            self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = self.kmeans.fit_predict(features_pca)
            
            # Analyze clusters
            df['cluster'] = cluster_labels
            cluster_results = []
            
            for cluster_id in range(n_clusters):
                cluster_cities = df[df['cluster'] == cluster_id]['city_name'].tolist()
                cluster_data = df[df['cluster'] == cluster_id][feature_columns]
                
                # Calculate cluster characteristics
                characteristics = {
                    'avg_temperature': float(cluster_data['temperature'].mean()),
                    'avg_humidity': float(cluster_data['humidity'].mean()),
                    'avg_wind_speed': float(cluster_data['wind_speed'].mean()),
                    'avg_pressure': float(cluster_data['pressure'].mean())
                }
                
                # Get cluster profile or create default
                profile = self.cluster_profiles.get(cluster_id, {
                    'name': f'Cluster {cluster_id}',
                    'emoji': '🌤️',
                    'desc': 'Mixed weather conditions'
                })
                
                cluster_results.append(ClusterResult(
                    cluster_id=cluster_id,
                    cluster_name=profile['name'],
                    cities=cluster_cities,
                    characteristics=characteristics,
                    emoji=profile['emoji'],
                    description=profile['desc']
                ))
            
            logger.info(f"Performed clustering analysis with {n_clusters} clusters")
            return cluster_results
            
        except Exception as e:
            logger.error(f"Error performing weather clustering: {e}")
            return []
    
    def recommend_city_by_preferences(self, 
                                    preferences: Dict[str, Any], 
                                    weather_profiles: List[WeatherProfile]) -> Optional[RecommendationResult]:
        """Recommend a city based on user weather preferences."""
        try:
            df = self.prepare_weather_data(weather_profiles)
            if df.empty:
                return None
            
            # Create preference vector
            pref_vector = np.array([
                preferences.get('temperature', 20),
                preferences.get('humidity', 50),
                preferences.get('wind_speed', 5),
                preferences.get('pressure', 1013),
                preferences.get('uv_index', 5),
                preferences.get('visibility', 10)
            ]).reshape(1, -1)
            
            # Normalize preference vector
            feature_columns = ['temperature', 'humidity', 'wind_speed', 'pressure', 'uv_index', 'visibility']
            features = df[feature_columns].values
            features_scaled = self.scaler.fit_transform(features)
            pref_scaled = self.scaler.transform(pref_vector)
            
            # Find nearest neighbors
            self.nn_model.fit(features_scaled)
            distances, indices = self.nn_model.kneighbors(pref_scaled)
            
            # Get best match
            best_match_idx = indices[0][0]
            best_match_distance = distances[0][0]
            
            recommended_city = df.iloc[best_match_idx]['city_name']
            match_percentage = max(0, (1 - best_match_distance) * 100)
            
            # Generate reasons
            city_data = df.iloc[best_match_idx]
            reasons = []
            
            temp_diff = abs(city_data['temperature'] - preferences.get('temperature', 20))
            if temp_diff < 5:
                reasons.append(f"Temperature matches your preference ({city_data['temperature']:.1f}°C)")
            
            humidity_diff = abs(city_data['humidity'] - preferences.get('humidity', 50))
            if humidity_diff < 15:
                reasons.append(f"Humidity level is ideal ({city_data['humidity']:.1f}%)")
            
            wind_diff = abs(city_data['wind_speed'] - preferences.get('wind_speed', 5))
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
                    description="Standard weather conditions"
                )
            
            # Comparison data
            comparison_data = {
                'your_preferences': preferences,
                'recommended_city_data': {
                    'temperature': float(city_data['temperature']),
                    'humidity': float(city_data['humidity']),
                    'wind_speed': float(city_data['wind_speed']),
                    'pressure': float(city_data['pressure'])
                },
                'differences': {
                    'temperature': float(temp_diff),
                    'humidity': float(humidity_diff),
                    'wind_speed': float(wind_diff)
                }
            }
            
            return RecommendationResult(
                recommended_city=recommended_city,
                match_percentage=match_percentage,
                reasons=reasons,
                cluster_info=cluster_info,
                comparison_data=comparison_data
            )
            
        except Exception as e:
            logger.error(f"Error generating city recommendation: {e}")
            return None
    
    def create_similarity_heatmap(self, weather_profiles: List[WeatherProfile], figsize=(10, 8), theme=None) -> plt.Figure:
        """Create a similarity heatmap visualization with theme support."""
        try:
            df = self.prepare_weather_data(weather_profiles)
            similarity_matrix = self.calculate_similarity_matrix(weather_profiles)
            
            # Apply theme settings
            self._apply_chart_theme(theme)
            
            if df.empty or similarity_matrix.size == 0:
                fig, ax = plt.subplots(figsize=figsize)
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes,
                       color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
                self._style_figure(fig, ax, theme)
                return fig
            
            # Create heatmap
            fig, ax = plt.subplots(figsize=figsize)
            
            city_names = df['city_name'].tolist()
            
            # Create custom colormap based on theme
            if theme:
                primary_color = theme.get('primary', '#00FF41')
                secondary_color = theme.get('secondary', '#008F11')
                # Create a custom colormap using theme colors
                from matplotlib.colors import LinearSegmentedColormap
                colors = ['#000000', secondary_color, primary_color]
                n_bins = 100
                cmap = LinearSegmentedColormap.from_list('theme_cmap', colors, N=n_bins)
            else:
                cmap = 'RdYlBu_r'
            
            # Create heatmap with seaborn
            sns.heatmap(
                similarity_matrix,
                annot=True,
                fmt='.2f',
                cmap=cmap,
                xticklabels=city_names,
                yticklabels=city_names,
                ax=ax,
                cbar_kws={'label': 'Similarity Score'},
                annot_kws={'color': theme.get('text', '#E0E0E0') if theme else '#E0E0E0'}
            )
            
            self._style_figure(fig, ax, theme)
            ax.set_title('🔥 City Weather Similarity Heatmap', fontsize=16, fontweight='bold',
                        color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            ax.set_xlabel('Cities', fontsize=12, color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            ax.set_ylabel('Cities', fontsize=12, color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            plt.tight_layout()
            
            logger.info("Created similarity heatmap")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating similarity heatmap: {e}")
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center', transform=ax.transAxes,
                   color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            self._style_figure(fig, ax, theme)
            return fig
    
    def create_cluster_visualization(self, weather_profiles: List[WeatherProfile], figsize=(12, 8), theme=None) -> plt.Figure:
        """Create cluster visualization with PCA and theme support."""
        try:
            # Apply theme settings
            self._apply_chart_theme(theme)
            
            df = self.prepare_weather_data(weather_profiles)
            if df.empty:
                fig, ax = plt.subplots(figsize=figsize)
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes,
                       color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
                self._style_figure(fig, ax, theme)
                return fig
            
            # Perform clustering
            clusters = self.perform_weather_clustering(weather_profiles)
            
            # Prepare features for PCA visualization
            feature_columns = ['temperature', 'humidity', 'wind_speed', 'pressure', 'uv_index']
            features = df[feature_columns].values
            features_scaled = self.scaler.fit_transform(features)
            
            # Apply PCA for 2D visualization
            pca_2d = PCA(n_components=2)
            features_2d = pca_2d.fit_transform(features_scaled)
            
            # Create visualization
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
            
            # Generate theme-based colors for clusters
            if theme:
                primary = theme.get('primary', '#00FF41')
                secondary = theme.get('secondary', '#008F11')
                accent = theme.get('accent', '#FF6B35')
                chart_colors = theme.get('chart_colors', [primary, secondary, accent, '#FFD700', '#FF69B4', '#00CED1'])
                colors = chart_colors[:len(clusters)] if len(clusters) <= len(chart_colors) else plt.cm.Set3(np.linspace(0, 1, len(clusters)))
            else:
                colors = plt.cm.Set3(np.linspace(0, 1, len(clusters)))
            
            # Cluster scatter plot
            for i, cluster in enumerate(clusters):
                cluster_indices = df[df['city_name'].isin(cluster.cities)].index
                if len(cluster_indices) > 0:
                    color = colors[i] if isinstance(colors, list) else colors[i]
                    ax1.scatter(
                        features_2d[cluster_indices, 0],
                        features_2d[cluster_indices, 1],
                        c=[color],
                        label=f"{cluster.emoji} {cluster.cluster_name}",
                        s=100,
                        alpha=0.8,
                        edgecolors=theme.get('text', '#E0E0E0') if theme else '#E0E0E0',
                        linewidth=1
                    )
                    
                    # Add city labels
                    for idx in cluster_indices:
                        ax1.annotate(
                            df.iloc[idx]['city_name'],
                            (features_2d[idx, 0], features_2d[idx, 1]),
                            xytext=(5, 5),
                            textcoords='offset points',
                            fontsize=8,
                            alpha=0.9,
                            color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0',
                            weight='bold'
                        )
            
            self._style_figure(fig, ax1, theme)
            ax1.set_title('🌍 Weather Clusters (PCA Visualization)', fontsize=14, fontweight='bold',
                         color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            ax1.set_xlabel(f'PC1 ({pca_2d.explained_variance_ratio_[0]:.1%} variance)',
                          color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            ax1.set_ylabel(f'PC2 ({pca_2d.explained_variance_ratio_[1]:.1%} variance)',
                          color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left',
                      facecolor=theme.get('card_bg', '#1E1E1E') if theme else '#1E1E1E',
                      edgecolor=theme.get('primary', '#00FF41') if theme else '#00FF41',
                      labelcolor=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            ax1.grid(True, alpha=0.3, color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            
            # Cluster characteristics bar chart
            cluster_names = [f"{c.emoji} {c.cluster_name}" for c in clusters]
            avg_temps = [c.characteristics.get('avg_temperature', 0) for c in clusters]
            
            # Use theme colors for bars
            bar_colors = colors[:len(clusters)] if isinstance(colors, list) else [colors[i] for i in range(len(clusters))]
            bars = ax2.bar(range(len(cluster_names)), avg_temps, color=bar_colors, alpha=0.8,
                          edgecolor=theme.get('text', '#E0E0E0') if theme else '#E0E0E0', linewidth=1)
            
            self._style_figure(fig, ax2, theme)
            ax2.set_title('📊 Average Temperature by Cluster', fontsize=14, fontweight='bold',
                         color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            ax2.set_xlabel('Weather Clusters', color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            ax2.set_ylabel('Average Temperature (°C)', color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            ax2.set_xticks(range(len(cluster_names)))
            ax2.set_xticklabels(cluster_names, rotation=45, ha='right',
                               color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            ax2.grid(True, alpha=0.3, color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            
            # Add value labels on bars
            for bar, temp in zip(bars, avg_temps):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        f'{temp:.1f}°C', ha='center', va='bottom', fontsize=10,
                        color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0', weight='bold')
            
            plt.tight_layout()
            
            logger.info("Created cluster visualization")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating cluster visualization: {e}")
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center', transform=ax.transAxes,
                   color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            self._style_figure(fig, ax, theme)
            return fig
    
    def create_radar_chart(self, weather_profiles: List[WeatherProfile], selected_cities: List[str] = None, figsize=(10, 10), theme=None) -> plt.Figure:
        """Create radar chart for weather comparison with theme support."""
        try:
            # Apply theme settings
            self._apply_chart_theme(theme)
            
            df = self.prepare_weather_data(weather_profiles)
            if df.empty:
                fig, ax = plt.subplots(figsize=figsize)
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes,
                       color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
                self._style_figure(fig, ax, theme)
                return fig
            
            # Filter for selected cities if provided
            if selected_cities:
                df = df[df['city_name'].isin(selected_cities)]
            
            if df.empty:
                fig, ax = plt.subplots(figsize=figsize)
                ax.text(0.5, 0.5, 'No cities selected', ha='center', va='center', transform=ax.transAxes,
                       color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
                self._style_figure(fig, ax, theme)
                return fig
            
            # Prepare radar chart data
            categories = ['🌡️ Temperature', '💧 Humidity', '💨 Wind Speed', '🌊 Pressure', '☀️ UV Index']
            
            # Normalize data to 0-100 scale for radar chart
            normalized_data = df.copy()
            normalized_data['temperature'] = (df['temperature'] + 20) / 60 * 100  # -20 to 40°C -> 0-100
            normalized_data['humidity'] = df['humidity']  # Already 0-100
            normalized_data['wind_speed'] = df['wind_speed'] / 20 * 100  # 0-20 m/s -> 0-100
            normalized_data['pressure'] = (df['pressure'] - 950) / 100 * 100  # 950-1050 hPa -> 0-100
            normalized_data['uv_index'] = df['uv_index'] / 12 * 100  # 0-12 -> 0-100
            
            # Create radar chart
            fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(projection='polar'))
            
            # Calculate angles for each category
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            angles += angles[:1]  # Complete the circle
            
            # Generate theme-based colors for cities
            if theme:
                primary = theme.get('primary', '#00FF41')
                secondary = theme.get('secondary', '#008F11')
                accent = theme.get('accent', '#FF6B35')
                chart_colors = theme.get('chart_colors', [primary, secondary, accent, '#FFD700', '#FF69B4', '#00CED1'])
                colors = chart_colors[:len(df)] if len(df) <= len(chart_colors) else plt.cm.Set3(np.linspace(0, 1, len(df)))
            else:
                colors = plt.cm.Set3(np.linspace(0, 1, len(df)))
            
            # Plot each city
            for i, (_, city_data) in enumerate(df.iterrows()):
                values = [
                    normalized_data.iloc[i]['temperature'],
                    normalized_data.iloc[i]['humidity'],
                    normalized_data.iloc[i]['wind_speed'],
                    normalized_data.iloc[i]['pressure'],
                    normalized_data.iloc[i]['uv_index']
                ]
                values += values[:1]  # Complete the circle
                
                color = colors[i] if isinstance(colors, list) else colors[i]
                ax.plot(angles, values, 'o-', linewidth=3, label=city_data['city_name'], color=color, markersize=8)
                ax.fill(angles, values, alpha=0.15, color=color)
            
            # Apply theme styling to polar chart
            self._style_polar_chart(ax, theme)
            
            # Customize the chart
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0', fontsize=11)
            ax.set_ylim(0, 100)
            ax.set_yticks([20, 40, 60, 80, 100])
            ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], 
                              color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0', fontsize=9)
            ax.grid(True, alpha=0.3, color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            
            plt.title('🎯 Weather Profile Comparison\n(Radar Chart)', size=16, fontweight='bold', pad=20,
                     color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0),
                      facecolor=theme.get('card_bg', '#1E1E1E') if theme else '#1E1E1E',
                      edgecolor=theme.get('primary', '#00FF41') if theme else '#00FF41',
                      labelcolor=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            
            logger.info("Created radar chart")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating radar chart: {e}")
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, f'Error: {str(e)}', ha='center', va='center', transform=ax.transAxes,
                   color=theme.get('text', '#E0E0E0') if theme else '#E0E0E0')
            self._style_figure(fig, ax, theme)
            return fig
    
    def _apply_chart_theme(self, theme):
        """Apply theme settings to matplotlib."""
        if theme:
            plt.rcParams.update({
                'figure.facecolor': theme.get('bg', '#000000'),
                'axes.facecolor': theme.get('card_bg', '#1E1E1E'),
                'axes.edgecolor': theme.get('primary', '#00FF41'),
                'axes.labelcolor': theme.get('text', '#E0E0E0'),
                'xtick.color': theme.get('text', '#E0E0E0'),
                'ytick.color': theme.get('text', '#E0E0E0'),
                'text.color': theme.get('text', '#E0E0E0'),
                'axes.spines.left': True,
                'axes.spines.bottom': True,
                'axes.spines.top': False,
                'axes.spines.right': False,
                'axes.linewidth': 1.5
            })
    
    def _style_figure(self, fig, ax, theme):
        """Apply theme styling to a figure and axes."""
        if theme:
            fig.patch.set_facecolor(theme.get('bg', '#000000'))
            ax.set_facecolor(theme.get('card_bg', '#1E1E1E'))
            
            # Style spines
            for spine in ax.spines.values():
                spine.set_color(theme.get('primary', '#00FF41'))
                spine.set_linewidth(1.5)
            
            # Hide top and right spines
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Style ticks
            ax.tick_params(colors=theme.get('text', '#E0E0E0'), which='both')
    
    def _style_polar_chart(self, ax, theme):
        """Apply theme styling to a polar chart."""
        if theme:
            ax.set_facecolor(theme.get('card_bg', '#1E1E1E'))
            ax.figure.patch.set_facecolor(theme.get('bg', '#000000'))
            
            # Style radial grid lines
            ax.tick_params(colors=theme.get('text', '#E0E0E0'))
            
            # Style the polar plot border
            ax.spines['polar'].set_color(theme.get('primary', '#00FF41'))
            ax.spines['polar'].set_linewidth(2)