"""Configuration enums and constants for Disaster Management Routing System."""
from enum import Enum


class RoadStatus(str, Enum):
    ACCESSIBLE = "ACCESSIBLE"
    PARTIALLY_BLOCKED = "PARTIALLY_BLOCKED"
    IMPASSABLE = "IMPASSABLE"


class RoadType(str, Enum):
    HIGHWAY = "HIGHWAY"
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    DIRT_TRACK = "DIRT_TRACK"


class DataProvenance(str, Enum):
    LIVE = "LIVE"
    HISTORICAL = "HISTORICAL"
    SIMULATED = "SIMULATED"


class HazardType(str, Enum):
    LANDSLIDE = "LANDSLIDE"
    FLOOD = "FLOOD"
    ROCKFALL = "ROCKFALL"
    BRIDGE_COLLAPSE = "BRIDGE_COLLAPSE"
