"""Export Data Transfer Objects

DTOs for data export formats (CSV, JSON, XML, PDF reports).
"""

import csv
import io
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ExportFormat(Enum):
    """Export format types."""

    CSV = "csv"
    JSON = "json"
    XML = "xml"
    PDF = "pdf"
    EXCEL = "xlsx"
    HTML = "html"


class ExportScope(Enum):
    """Export data scope."""

    CURRENT = "current"
    FORECAST = "forecast"
    HISTORICAL = "historical"
    ALERTS = "alerts"
    ALL = "all"


@dataclass
class ExportMetadataDTO:
    """Export metadata DTO."""

    export_id: str
    format: ExportFormat
    scope: ExportScope
    generated_at: datetime
    generated_by: str
    location: str
    date_range: Optional[str] = None
    record_count: int = 0
    file_size_bytes: Optional[int] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "export_id": self.export_id,
            "format": self.format.value,
            "scope": self.scope.value,
            "generated_at": self.generated_at.isoformat(),
            "generated_by": self.generated_by,
            "location": self.location,
            "date_range": self.date_range,
            "record_count": self.record_count,
            "file_size_bytes": self.file_size_bytes,
            "description": self.description,
        }


@dataclass
class WeatherExportRecordDTO:
    """Single weather record for export."""

    timestamp: datetime
    location_name: str
    latitude: float
    longitude: float
    temperature_celsius: float
    temperature_fahrenheit: float
    feels_like_celsius: float
    feels_like_fahrenheit: float
    humidity: int
    pressure_hpa: float
    pressure_inhg: float
    wind_speed_mps: float
    wind_speed_kmh: float
    wind_speed_mph: float
    wind_direction_degrees: Optional[float]
    wind_direction_text: str
    visibility_km: Optional[float]
    uv_index: Optional[float]
    weather_condition: str
    weather_description: str
    weather_icon: str
    is_day: bool
    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None

    def to_csv_row(self) -> List[str]:
        """Convert to CSV row."""
        return [
            self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            self.location_name,
            str(self.latitude),
            str(self.longitude),
            str(self.temperature_celsius),
            str(self.temperature_fahrenheit),
            str(self.feels_like_celsius),
            str(self.feels_like_fahrenheit),
            str(self.humidity),
            str(self.pressure_hpa),
            str(self.pressure_inhg),
            str(self.wind_speed_mps),
            str(self.wind_speed_kmh),
            str(self.wind_speed_mph),
            str(self.wind_direction_degrees) if self.wind_direction_degrees else "",
            self.wind_direction_text,
            str(self.visibility_km) if self.visibility_km else "",
            str(self.uv_index) if self.uv_index else "",
            self.weather_condition,
            self.weather_description,
            self.weather_icon,
            str(self.is_day),
            self.sunrise.strftime("%Y-%m-%d %H:%M:%S") if self.sunrise else "",
            self.sunset.strftime("%Y-%m-%d %H:%M:%S") if self.sunset else "",
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "location": {
                "name": self.location_name,
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            "temperature": {
                "celsius": self.temperature_celsius,
                "fahrenheit": self.temperature_fahrenheit,
                "feels_like_celsius": self.feels_like_celsius,
                "feels_like_fahrenheit": self.feels_like_fahrenheit,
            },
            "atmospheric": {
                "humidity": self.humidity,
                "pressure_hpa": self.pressure_hpa,
                "pressure_inhg": self.pressure_inhg,
                "visibility_km": self.visibility_km,
                "uv_index": self.uv_index,
            },
            "wind": {
                "speed_mps": self.wind_speed_mps,
                "speed_kmh": self.wind_speed_kmh,
                "speed_mph": self.wind_speed_mph,
                "direction_degrees": self.wind_direction_degrees,
                "direction_text": self.wind_direction_text,
            },
            "weather": {
                "condition": self.weather_condition,
                "description": self.weather_description,
                "icon": self.weather_icon,
                "is_day": self.is_day,
            },
            "sun_times": {
                "sunrise": self.sunrise.isoformat() if self.sunrise else None,
                "sunset": self.sunset.isoformat() if self.sunset else None,
            },
        }

    @classmethod
    def csv_headers(cls) -> List[str]:
        """Get CSV headers."""
        return [
            "timestamp",
            "location_name",
            "latitude",
            "longitude",
            "temperature_celsius",
            "temperature_fahrenheit",
            "feels_like_celsius",
            "feels_like_fahrenheit",
            "humidity",
            "pressure_hpa",
            "pressure_inhg",
            "wind_speed_mps",
            "wind_speed_kmh",
            "wind_speed_mph",
            "wind_direction_degrees",
            "wind_direction_text",
            "visibility_km",
            "uv_index",
            "weather_condition",
            "weather_description",
            "weather_icon",
            "is_day",
            "sunrise",
            "sunset",
        ]


@dataclass
class ForecastExportRecordDTO:
    """Forecast record for export."""

    forecast_timestamp: datetime
    forecast_date: date
    forecast_hour: int
    location_name: str
    latitude: float
    longitude: float
    temperature_celsius: float
    temperature_fahrenheit: float
    min_temp_celsius: Optional[float]
    max_temp_celsius: Optional[float]
    min_temp_fahrenheit: Optional[float]
    max_temp_fahrenheit: Optional[float]
    humidity: int
    pressure_hpa: float
    wind_speed_mps: float
    wind_direction_degrees: Optional[float]
    precipitation_probability: Optional[float]
    precipitation_mm: Optional[float]
    weather_condition: str
    weather_description: str
    weather_icon: str
    forecast_type: str  # hourly, daily

    def to_csv_row(self) -> List[str]:
        """Convert to CSV row."""
        return [
            self.forecast_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            self.forecast_date.strftime("%Y-%m-%d"),
            str(self.forecast_hour),
            self.location_name,
            str(self.latitude),
            str(self.longitude),
            str(self.temperature_celsius),
            str(self.temperature_fahrenheit),
            str(self.min_temp_celsius) if self.min_temp_celsius else "",
            str(self.max_temp_celsius) if self.max_temp_celsius else "",
            str(self.min_temp_fahrenheit) if self.min_temp_fahrenheit else "",
            str(self.max_temp_fahrenheit) if self.max_temp_fahrenheit else "",
            str(self.humidity),
            str(self.pressure_hpa),
            str(self.wind_speed_mps),
            str(self.wind_direction_degrees) if self.wind_direction_degrees else "",
            str(self.precipitation_probability) if self.precipitation_probability else "",
            str(self.precipitation_mm) if self.precipitation_mm else "",
            self.weather_condition,
            self.weather_description,
            self.weather_icon,
            self.forecast_type,
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "forecast_timestamp": self.forecast_timestamp.isoformat(),
            "forecast_date": self.forecast_date.isoformat(),
            "forecast_hour": self.forecast_hour,
            "location": {
                "name": self.location_name,
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            "temperature": {
                "celsius": self.temperature_celsius,
                "fahrenheit": self.temperature_fahrenheit,
                "min_celsius": self.min_temp_celsius,
                "max_celsius": self.max_temp_celsius,
                "min_fahrenheit": self.min_temp_fahrenheit,
                "max_fahrenheit": self.max_temp_fahrenheit,
            },
            "atmospheric": {"humidity": self.humidity, "pressure_hpa": self.pressure_hpa},
            "wind": {
                "speed_mps": self.wind_speed_mps,
                "direction_degrees": self.wind_direction_degrees,
            },
            "precipitation": {
                "probability": self.precipitation_probability,
                "amount_mm": self.precipitation_mm,
            },
            "weather": {
                "condition": self.weather_condition,
                "description": self.weather_description,
                "icon": self.weather_icon,
            },
            "forecast_type": self.forecast_type,
        }

    @classmethod
    def csv_headers(cls) -> List[str]:
        """Get CSV headers."""
        return [
            "forecast_timestamp",
            "forecast_date",
            "forecast_hour",
            "location_name",
            "latitude",
            "longitude",
            "temperature_celsius",
            "temperature_fahrenheit",
            "min_temp_celsius",
            "max_temp_celsius",
            "min_temp_fahrenheit",
            "max_temp_fahrenheit",
            "humidity",
            "pressure_hpa",
            "wind_speed_mps",
            "wind_direction_degrees",
            "precipitation_probability",
            "precipitation_mm",
            "weather_condition",
            "weather_description",
            "weather_icon",
            "forecast_type",
        ]


@dataclass
class AlertExportRecordDTO:
    """Alert record for export."""

    alert_id: str
    timestamp: datetime
    location_name: str
    latitude: float
    longitude: float
    event_type: str
    severity: str
    urgency: str
    certainty: str
    title: str
    description: str
    instructions: Optional[str]
    start_time: datetime
    end_time: datetime
    duration_hours: float
    source: str
    areas_affected: List[str]
    is_active: bool

    def to_csv_row(self) -> List[str]:
        """Convert to CSV row."""
        return [
            self.alert_id,
            self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            self.location_name,
            str(self.latitude),
            str(self.longitude),
            self.event_type,
            self.severity,
            self.urgency,
            self.certainty,
            self.title,
            self.description,
            self.instructions or "",
            self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            self.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            str(self.duration_hours),
            self.source,
            "; ".join(self.areas_affected),
            str(self.is_active),
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp.isoformat(),
            "location": {
                "name": self.location_name,
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            "event": {
                "type": self.event_type,
                "severity": self.severity,
                "urgency": self.urgency,
                "certainty": self.certainty,
            },
            "details": {
                "title": self.title,
                "description": self.description,
                "instructions": self.instructions,
            },
            "timing": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_hours": self.duration_hours,
            },
            "source": self.source,
            "areas_affected": self.areas_affected,
            "is_active": self.is_active,
        }

    @classmethod
    def csv_headers(cls) -> List[str]:
        """Get CSV headers."""
        return [
            "alert_id",
            "timestamp",
            "location_name",
            "latitude",
            "longitude",
            "event_type",
            "severity",
            "urgency",
            "certainty",
            "title",
            "description",
            "instructions",
            "start_time",
            "end_time",
            "duration_hours",
            "source",
            "areas_affected",
            "is_active",
        ]


@dataclass
class WeatherExportDTO:
    """Complete weather export DTO."""

    metadata: ExportMetadataDTO
    weather_records: List[WeatherExportRecordDTO] = field(default_factory=list)
    forecast_records: List[ForecastExportRecordDTO] = field(default_factory=list)
    alert_records: List[AlertExportRecordDTO] = field(default_factory=list)

    def to_csv(self) -> str:
        """Export to CSV format."""
        output = io.StringIO()

        # Write metadata
        output.write("# Weather Data Export\n")
        output.write(f"# Generated: {self.metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write(f"# Location: {self.metadata.location}\n")
        output.write(f"# Format: {self.metadata.format.value}\n")
        output.write(f"# Scope: {self.metadata.scope.value}\n")
        if self.metadata.date_range:
            output.write(f"# Date Range: {self.metadata.date_range}\n")
        output.write(f"# Records: {self.metadata.record_count}\n")
        output.write("\n")

        # Write weather records
        if self.weather_records:
            output.write("# Current Weather Data\n")
            writer = csv.writer(output)
            writer.writerow(WeatherExportRecordDTO.csv_headers())
            for record in self.weather_records:
                writer.writerow(record.to_csv_row())
            output.write("\n")

        # Write forecast records
        if self.forecast_records:
            output.write("# Forecast Data\n")
            writer = csv.writer(output)
            writer.writerow(ForecastExportRecordDTO.csv_headers())
            for record in self.forecast_records:
                writer.writerow(record.to_csv_row())
            output.write("\n")

        # Write alert records
        if self.alert_records:
            output.write("# Alert Data\n")
            writer = csv.writer(output)
            writer.writerow(AlertExportRecordDTO.csv_headers())
            for record in self.alert_records:
                writer.writerow(record.to_csv_row())

        return output.getvalue()

    def to_json(self, indent: int = 2) -> str:
        """Export to JSON format."""
        data = {
            "metadata": self.metadata.to_dict(),
            "data": {
                "weather_records": [record.to_dict() for record in self.weather_records],
                "forecast_records": [record.to_dict() for record in self.forecast_records],
                "alert_records": [record.to_dict() for record in self.alert_records],
            },
        }
        return json.dumps(data, indent=indent, default=str)

    def to_xml(self) -> str:
        """Export to XML format."""
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_lines.append("<weather_export>")

        # Metadata
        xml_lines.append("  <metadata>")
        xml_lines.append(f"    <export_id>{self.metadata.export_id}</export_id>")
        xml_lines.append(f"    <format>{self.metadata.format.value}</format>")
        xml_lines.append(f"    <scope>{self.metadata.scope.value}</scope>")
        xml_lines.append(
            f"    <generated_at>{self.metadata.generated_at.isoformat()}</generated_at>"
        )
        xml_lines.append(f"    <generated_by>{self.metadata.generated_by}</generated_by>")
        xml_lines.append(f"    <location>{self.metadata.location}</location>")
        if self.metadata.date_range:
            xml_lines.append(f"    <date_range>{self.metadata.date_range}</date_range>")
        xml_lines.append(f"    <record_count>{self.metadata.record_count}</record_count>")
        xml_lines.append("  </metadata>")

        # Weather records
        if self.weather_records:
            xml_lines.append("  <weather_records>")
            for record in self.weather_records:
                xml_lines.append("    <record>")
                xml_lines.append(f"      <timestamp>{record.timestamp.isoformat()}</timestamp>")
                xml_lines.append(f"      <location_name>{record.location_name}</location_name>")
                xml_lines.append(f"      <latitude>{record.latitude}</latitude>")
                xml_lines.append(f"      <longitude>{record.longitude}</longitude>")
                xml_lines.append(
                    f"      <temperature_celsius>{record.temperature_celsius}</temperature_celsius>"
                )
                xml_lines.append(
                    f"      <temperature_fahrenheit>{record.temperature_fahrenheit}</temperature_fahrenheit>"
                )
                xml_lines.append(f"      <humidity>{record.humidity}</humidity>")
                xml_lines.append(f"      <pressure_hpa>{record.pressure_hpa}</pressure_hpa>")
                xml_lines.append(f"      <wind_speed_mps>{record.wind_speed_mps}</wind_speed_mps>")
                xml_lines.append(
                    f"      <weather_condition>{record.weather_condition}</weather_condition>"
                )
                xml_lines.append(
                    f"      <weather_description>{record.weather_description}</weather_description>"
                )
                xml_lines.append("    </record>")
            xml_lines.append("  </weather_records>")

        # Forecast records
        if self.forecast_records:
            xml_lines.append("  <forecast_records>")
            for record in self.forecast_records:
                xml_lines.append("    <record>")
                xml_lines.append(
                    f"      <forecast_timestamp>{record.forecast_timestamp.isoformat()}</forecast_timestamp>"
                )
                xml_lines.append(f"      <location_name>{record.location_name}</location_name>")
                xml_lines.append(
                    f"      <temperature_celsius>{record.temperature_celsius}</temperature_celsius>"
                )
                xml_lines.append(
                    f"      <weather_condition>{record.weather_condition}</weather_condition>"
                )
                xml_lines.append(f"      <forecast_type>{record.forecast_type}</forecast_type>")
                xml_lines.append("    </record>")
            xml_lines.append("  </forecast_records>")

        # Alert records
        if self.alert_records:
            xml_lines.append("  <alert_records>")
            for record in self.alert_records:
                xml_lines.append("    <record>")
                xml_lines.append(f"      <alert_id>{record.alert_id}</alert_id>")
                xml_lines.append(f"      <timestamp>{record.timestamp.isoformat()}</timestamp>")
                xml_lines.append(f"      <event_type>{record.event_type}</event_type>")
                xml_lines.append(f"      <severity>{record.severity}</severity>")
                xml_lines.append(f"      <title>{record.title}</title>")
                xml_lines.append(f"      <is_active>{record.is_active}</is_active>")
                xml_lines.append("    </record>")
            xml_lines.append("  </alert_records>")

        xml_lines.append("</weather_export>")
        return "\n".join(xml_lines)

    def get_summary(self) -> Dict[str, Any]:
        """Get export summary."""
        return {
            "export_id": self.metadata.export_id,
            "format": self.metadata.format.value,
            "scope": self.metadata.scope.value,
            "generated_at": self.metadata.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "location": self.metadata.location,
            "total_records": len(self.weather_records)
            + len(self.forecast_records)
            + len(self.alert_records),
            "weather_records": len(self.weather_records),
            "forecast_records": len(self.forecast_records),
            "alert_records": len(self.alert_records),
            "date_range": self.metadata.date_range,
            "file_size_estimate": self._estimate_file_size(),
        }

    def _estimate_file_size(self) -> str:
        """Estimate file size based on format and record count."""
        total_records = (
            len(self.weather_records) + len(self.forecast_records) + len(self.alert_records)
        )

        if self.metadata.format == ExportFormat.CSV:
            # Rough estimate: 200 bytes per record for CSV
            size_bytes = total_records * 200
        elif self.metadata.format == ExportFormat.JSON:
            # Rough estimate: 500 bytes per record for JSON
            size_bytes = total_records * 500
        elif self.metadata.format == ExportFormat.XML:
            # Rough estimate: 400 bytes per record for XML
            size_bytes = total_records * 400
        else:
            size_bytes = total_records * 300

        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"


@dataclass
class ExportRequestDTO:
    """Export request DTO."""

    format: ExportFormat
    scope: ExportScope
    location: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_metadata: bool = True
    include_charts: bool = False
    timezone: str = "UTC"
    temperature_unit: str = "celsius"  # celsius, fahrenheit, both
    wind_unit: str = "mps"  # mps, kmh, mph
    pressure_unit: str = "hpa"  # hpa, inhg
    filename: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "format": self.format.value,
            "scope": self.scope.value,
            "location": self.location,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "include_metadata": self.include_metadata,
            "include_charts": self.include_charts,
            "timezone": self.timezone,
            "temperature_unit": self.temperature_unit,
            "wind_unit": self.wind_unit,
            "pressure_unit": self.pressure_unit,
            "filename": self.filename,
        }

    def get_filename(self) -> str:
        """Generate filename if not provided."""
        if self.filename:
            return self.filename

        # Generate filename based on scope and date
        base_name = f"weather_{self.scope.value}_{self.location.replace(' ', '_').lower()}"

        if self.start_date and self.end_date:
            date_part = f"_{self.start_date.strftime('%Y%m%d')}_{self.end_date.strftime('%Y%m%d')}"
        elif self.start_date:
            date_part = f"_{self.start_date.strftime('%Y%m%d')}"
        else:
            date_part = f"_{datetime.now().strftime('%Y%m%d')}"

        return f"{base_name}{date_part}.{self.format.value}"

    def validate(self) -> List[str]:
        """Validate export request."""
        errors = []

        if not self.location:
            errors.append("Location is required")

        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors.append("Start date must be before end date")

        if self.scope == ExportScope.HISTORICAL and not (self.start_date and self.end_date):
            errors.append("Historical export requires start and end dates")

        if self.temperature_unit not in ["celsius", "fahrenheit", "both"]:
            errors.append("Invalid temperature unit")

        if self.wind_unit not in ["mps", "kmh", "mph"]:
            errors.append("Invalid wind unit")

        if self.pressure_unit not in ["hpa", "inhg"]:
            errors.append("Invalid pressure unit")

        return errors


@dataclass
class ExportResponseDTO:
    """Export response DTO."""

    export_id: str
    status: str  # pending, processing, completed, failed
    filename: str
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress_percentage: int = 0
    estimated_completion: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "export_id": self.export_id,
            "status": self.status,
            "filename": self.filename,
            "file_size_bytes": self.file_size_bytes,
            "download_url": self.download_url,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "error_message": self.error_message,
            "progress_percentage": self.progress_percentage,
            "estimated_completion": (
                self.estimated_completion.isoformat() if self.estimated_completion else None
            ),
        }

    def is_ready(self) -> bool:
        """Check if export is ready for download."""
        return self.status == "completed" and self.download_url is not None

    def is_failed(self) -> bool:
        """Check if export failed."""
        return self.status == "failed"

    def is_processing(self) -> bool:
        """Check if export is still processing."""
        return self.status in ["pending", "processing"]
