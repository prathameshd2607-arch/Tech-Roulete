"""Streaming telemetry and spatial event generators for disaster simulation."""
from datetime import datetime, timedelta, timezone
import random
from typing import Generator, List, Tuple

from src.config import DataProvenance, HazardType
from src.schemas import (
    CrowdsourcedReport,
    Envelope,
    HistoricalHazardLog,
    RainfallMeasurement,
    RiverGaugeMeasurement,
)


def rainfall_stream_generator(
    settlement_ids: List[str],
) -> Generator[List[Envelope[RainfallMeasurement]], None, None]:
    """
    Yields continuous telemetry readings for 10 rainfall sensors mapped to settlements.
    Simulates dynamic weather patterns with fluctuating precipitation intensity.
    """
    # Baseline intensity per sensor
    base_intensities = {sid: random.uniform(5.0, 30.0) for sid in settlement_ids}

    while True:
        timestamp = datetime.now(timezone.utc)
        tick_measurements: List[Envelope[RainfallMeasurement]] = []

        for idx, sid in enumerate(settlement_ids, 1):
            # Dynamic fluctuation
            delta = random.uniform(-4.0, 5.5)
            base_intensities[sid] = max(0.0, min(140.0, base_intensities[sid] + delta))
            intensity = round(base_intensities[sid], 2)

            payload = RainfallMeasurement(
                sensor_id=f"RAIN-SN-{idx:02d}",
                settlement_id=sid,
                intensity_mm_hr=intensity,
                timestamp=timestamp,
            )

            envelope = Envelope[RainfallMeasurement](
                provenance=DataProvenance.SIMULATED,
                ingestion_timestamp=timestamp,
                payload=payload,
            )
            tick_measurements.append(envelope)

        yield tick_measurements


def river_gauge_stream_generator() -> Generator[List[Envelope[RiverGaugeMeasurement]], None, None]:
    """
    Yields telemetry from 3 river gauge monitoring stations along major hydrologic channels.
    Simulates stage level fluctuations against defined flood thresholds.
    """
    station_configs = [
        ("RG-TRISHULI-01", "Trishuli River", 3.2, 5.5),
        ("RG-MELAMCHI-02", "Melamchi River", 2.1, 4.0),
        ("RG-BHOTEKOSHI-03", "Bhote Koshi River", 4.0, 6.8),
    ]

    current_levels = {sid: initial_lvl for sid, _, initial_lvl, _ in station_configs}

    while True:
        timestamp = datetime.now(timezone.utc)
        tick_measurements: List[Envelope[RiverGaugeMeasurement]] = []

        for sid, rname, _, flood_thresh in station_configs:
            delta = random.uniform(-0.15, 0.25)
            current_levels[sid] = round(max(0.5, current_levels[sid] + delta), 2)

            payload = RiverGaugeMeasurement(
                station_id=sid,
                river_name=rname,
                level_meters=current_levels[sid],
                flood_threshold_meters=flood_thresh,
                timestamp=timestamp,
            )

            envelope = Envelope[RiverGaugeMeasurement](
                provenance=DataProvenance.SIMULATED,
                ingestion_timestamp=timestamp,
                payload=payload,
            )
            tick_measurements.append(envelope)

        yield tick_measurements


def load_historical_hazard_logs(
    num_records: int = 25,
) -> List[Envelope[HistoricalHazardLog]]:
    """
    Generate and load 25 historical hazard records for landslides, floods, rockfalls, etc.
    Distributed across the district bounding box over the preceding 5 years.
    """
    random.seed(101)
    records: List[Envelope[HistoricalHazardLog]] = []
    base_time = datetime(2021, 1, 1, tzinfo=timezone.utc)

    hazard_weights = [
        HazardType.LANDSLIDE,
        HazardType.LANDSLIDE,
        HazardType.FLOOD,
        HazardType.ROCKFALL,
        HazardType.BRIDGE_COLLAPSE,
    ]

    for i in range(1, num_records + 1):
        days_offset = random.randint(10, 1800)
        event_time = base_time + timedelta(days=days_offset, hours=random.randint(0, 23))

        lat = round(random.uniform(27.75, 28.00), 5)
        lon = round(random.uniform(85.00, 85.90), 5)
        hazard_type = random.choice(hazard_weights)
        severity = random.randint(1, 5)

        payload = HistoricalHazardLog(
            log_id=f"HIST-HZ-{i:04d}",
            hazard_type=hazard_type,
            location_coordinates=(lat, lon),
            date_occurred=event_time,
            severity_index=severity,
        )

        envelope = Envelope[HistoricalHazardLog](
            provenance=DataProvenance.SIMULATED,
            ingestion_timestamp=datetime.now(timezone.utc),
            payload=payload,
        )
        records.append(envelope)

    return records


def crowdsourced_report_stream_generator() -> Generator[Envelope[CrowdsourcedReport], None, None]:
    """
    Yields sporadic crowdsourced citizen observations and incident reports from the field.
    """
    descriptions = {
        HazardType.LANDSLIDE: [
            "Debris and boulders covering both lanes near the river bend.",
            "Mudslide triggered by heavy rain blocking access to uphill hamlet.",
            "Slope slip observed above highway, trees sliding down.",
        ],
        HazardType.FLOOD: [
            "River overflowed onto low bridge, water ~0.8m deep.",
            "Torrential stream washing out culvert on access road.",
            "Flash flooding near market settlement.",
        ],
        HazardType.ROCKFALL: [
            "Falling rocks from steep cliff face, single lane passable.",
            "Scattered rock debris damaging vehicle tires.",
        ],
        HazardType.BRIDGE_COLLAPSE: [
            "Suspension bridge abutment damaged by high water flow.",
            "Concrete culvert collapsed, completely impassable for four-wheelers.",
        ],
    }

    counter = 1
    while True:
        timestamp = datetime.now(timezone.utc)
        hazard_type = random.choice(list(HazardType))
        desc = random.choice(descriptions[hazard_type])
        lat = round(random.uniform(27.75, 28.00), 5)
        lon = round(random.uniform(85.00, 85.90), 5)
        reliability = round(random.uniform(0.45, 0.98), 2)

        payload = CrowdsourcedReport(
            report_id=f"CITIZEN-REP-{counter:05d}",
            timestamp=timestamp,
            location=(lat, lon),
            hazard_type=hazard_type,
            user_reliability_score=reliability,
            description=desc,
        )

        envelope = Envelope[CrowdsourcedReport](
            provenance=DataProvenance.SIMULATED,
            ingestion_timestamp=timestamp,
            payload=payload,
        )
        counter += 1
        yield envelope
