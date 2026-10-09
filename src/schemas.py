"""Pydantic schemas for disaster management spatial and telemetry data."""
from datetime import datetime, timezone
from typing import Generic, Tuple, TypeVar
from pydantic import BaseModel, Field

from src.config import DataProvenance, HazardType, RoadStatus, RoadType

T = TypeVar("T")


class Settlement(BaseModel):
    id: str = Field(..., description="Unique settlement identifier")
    name: str = Field(..., description="Name of the settlement")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate in EPSG:4326")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate in EPSG:4326")
    population: int = Field(..., ge=0, description="Population count")
    elevation_m: float = Field(..., description="Elevation above sea level in meters")
    slope_deg: float = Field(..., ge=0.0, le=90.0, description="Topographical slope angle in degrees")


class RoadSegment(BaseModel):
    source_id: str = Field(..., description="Source settlement ID")
    target_id: str = Field(..., description="Target settlement ID")
    road_type: RoadType = Field(..., description="Classification of the road segment")
    length_km: float = Field(..., gt=0.0, description="Physical segment length in kilometers")
    status: RoadStatus = Field(..., description="Current operational status of the road")
    max_speed_kmh: float = Field(..., gt=0.0, description="Maximum speed limit in km/h")


class RainfallMeasurement(BaseModel):
    sensor_id: str = Field(..., description="Unique rain gauge sensor identifier")
    settlement_id: str = Field(..., description="Associated settlement identifier")
    intensity_mm_hr: float = Field(..., ge=0.0, description="Rainfall intensity rate in mm/hour")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Measurement timestamp")


class RiverGaugeMeasurement(BaseModel):
    station_id: str = Field(..., description="River hydrometric station ID")
    river_name: str = Field(..., description="Name of the river monitored")
    level_meters: float = Field(..., ge=0.0, description="Current water stage level in meters")
    flood_threshold_meters: float = Field(..., gt=0.0, description="Threshold level triggering flood alerts")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Measurement timestamp")


class HistoricalHazardLog(BaseModel):
    log_id: str = Field(..., description="Historical hazard record ID")
    hazard_type: HazardType = Field(..., description="Type of historical hazard event")
    location_coordinates: Tuple[float, float] = Field(..., description="(latitude, longitude) coordinates")
    date_occurred: datetime = Field(..., description="Date and time when the hazard occurred")
    severity_index: int = Field(..., ge=1, le=5, description="Hazard severity level from 1 (minor) to 5 (catastrophic)")


class CrowdsourcedReport(BaseModel):
    report_id: str = Field(..., description="Unique report identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Report submission timestamp")
    location: Tuple[float, float] = Field(..., description="(latitude, longitude) of observed event")
    hazard_type: HazardType = Field(..., description="Reported hazard category")
    user_reliability_score: float = Field(..., ge=0.0, le=1.0, description="Confidence/reliability score of reporting citizen")
    description: str = Field(..., description="Descriptive ground report details")


class Envelope(BaseModel, Generic[T]):
    provenance: DataProvenance = Field(..., description="Data lineage and provenance indicator")
    ingestion_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when data was ingested into the system"
    )
    payload: T = Field(..., description="Typed telemetry or spatial payload")
