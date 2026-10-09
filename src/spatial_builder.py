"""Spatial data builder for district geography and road network topology."""
import math
import random
from typing import Dict, List, Tuple
import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString, Point

from src.config import RoadStatus, RoadType
from src.schemas import Settlement


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth (in km)."""
    r = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def generate_district_data() -> gpd.GeoDataFrame:
    """
    Generate 10 settlements in a realistic mountain district cluster (e.g., Central Himalayas).
    Returns a GeoPandas GeoDataFrame with attributes and Point geometries in EPSG:4326.
    """
    random.seed(42)  # For reproducible spatial layout

    settlement_templates = [
        ("S01", "Trishuli Valley", 27.8021, 85.1432, 12500, 620.0, 8.5),
        ("S02", "Dhading Ridge", 27.8745, 85.0214, 8400, 1420.0, 18.2),
        ("S03", "Nuwakot Hilltop", 27.9150, 85.1670, 6200, 1780.0, 24.0),
        ("S04", "Langtang Foothills", 27.9850, 85.3120, 3100, 2850.0, 38.5),
        ("S05", "Melamchi Basin", 27.8310, 85.5780, 7800, 890.0, 12.0),
        ("S06", "Helambu Highland", 27.9620, 85.4950, 2400, 3120.0, 41.2),
        ("S07", "Sundarijal Outpost", 27.7650, 85.4210, 4500, 1550.0, 19.8),
        ("S08", "Chautara Summit", 27.7780, 85.7140, 9200, 1620.0, 22.4),
        ("S09", "Bahrabise Gorge", 27.7920, 85.8950, 5600, 980.0, 33.0),
        ("S10", "Gosaikunda Pass Junction", 27.9950, 85.2150, 1200, 3190.0, 39.7),
    ]

    records = []
    geometries = []

    for sid, name, lat, lon, pop, elev, slope in settlement_templates:
        # Validate through Pydantic schema
        settlement = Settlement(
            id=sid,
            name=name,
            latitude=lat,
            longitude=lon,
            population=pop,
            elevation_m=elev,
            slope_deg=slope,
        )
        records.append(settlement.model_dump())
        geometries.append(Point(lon, lat))

    gdf = gpd.GeoDataFrame(records, geometry=geometries, crs="EPSG:4326")
    return gdf


def build_road_graph(settlements_gdf: gpd.GeoDataFrame) -> nx.Graph:
    """
    Construct a connected road network graph among all settlements.
    Guarantees a single connected component using Minimum Spanning Tree + arterial loops.
    Assigns road types, terrain-adjusted lengths, speed limits, and operational statuses (80% accessible, 20% blocked/impassable).
    """
    random.seed(42)
    graph = nx.Graph()

    # Add nodes with attributes
    nodes_dict: Dict[str, dict] = {}
    for _, row in settlements_gdf.iterrows():
        node_id = row["id"]
        node_attr = {
            "id": node_id,
            "name": row["name"],
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "population": int(row["population"]),
            "elevation_m": float(row["elevation_m"]),
            "slope_deg": float(row["slope_deg"]),
        }
        graph.add_node(node_id, **node_attr)
        nodes_dict[node_id] = node_attr

    node_ids = list(nodes_dict.keys())
    n = len(node_ids)

    # Compute complete pairwise distance graph
    complete_graph = nx.Graph()
    for i in range(n):
        for j in range(i + 1, n):
            u, v = node_ids[i], node_ids[j]
            dist = haversine_distance(
                nodes_dict[u]["latitude"],
                nodes_dict[u]["longitude"],
                nodes_dict[v]["latitude"],
                nodes_dict[v]["longitude"],
            )
            complete_graph.add_edge(u, v, weight=dist)

    # 1. Guarantee single connected component via Minimum Spanning Tree
    mst = nx.minimum_spanning_tree(complete_graph, weight="weight")
    candidate_edges = set(tuple(sorted((u, v))) for u, v in mst.edges())

    # 2. Add realistic k-nearest neighbor neighbor loops (mountain valley shortcuts)
    for u in node_ids:
        # Find 3 closest neighbors
        neighbors = sorted(
            [v for v in node_ids if v != u],
            key=lambda v: complete_graph[u][v]["weight"],
        )[:3]
        for v in neighbors:
            candidate_edges.add(tuple(sorted((u, v))))

    edge_list = list(candidate_edges)
    random.shuffle(edge_list)
    total_edges = len(edge_list)

    # Calculate status breakdown: exactly ~80% ACCESSIBLE, 20% disrupted
    num_disrupted = max(1, int(round(total_edges * 0.20)))
    num_accessible = total_edges - num_disrupted

    statuses = [RoadStatus.ACCESSIBLE] * num_accessible
    # Distribute disrupted between PARTIALLY_BLOCKED and IMPASSABLE
    partially_blocked_count = num_disrupted // 2
    impassable_count = num_disrupted - partially_blocked_count
    statuses.extend([RoadStatus.PARTIALLY_BLOCKED] * partially_blocked_count)
    statuses.extend([RoadStatus.IMPASSABLE] * impassable_count)
    random.shuffle(statuses)

    road_types_pool = [
        RoadType.HIGHWAY,
        RoadType.PRIMARY,
        RoadType.PRIMARY,
        RoadType.SECONDARY,
        RoadType.SECONDARY,
        RoadType.DIRT_TRACK,
    ]

    speed_lookup = {
        RoadType.HIGHWAY: 80.0,
        RoadType.PRIMARY: 60.0,
        RoadType.SECONDARY: 40.0,
        RoadType.DIRT_TRACK: 25.0,
    }

    for idx, (u, v) in enumerate(edge_list):
        base_dist = complete_graph[u][v]["weight"]
        # Mountain sinuosity factor between 1.15 and 1.35x
        sinuosity = random.uniform(1.15, 1.35)
        length_km = round(base_dist * sinuosity, 2)

        # Assign road type based on elevation/slope or distance
        u_slope = nodes_dict[u]["slope_deg"]
        v_slope = nodes_dict[v]["slope_deg"]
        avg_slope = (u_slope + v_slope) / 2.0

        if avg_slope > 30.0:
            road_type = random.choice([RoadType.SECONDARY, RoadType.DIRT_TRACK])
        elif length_km > 30.0:
            road_type = random.choice([RoadType.HIGHWAY, RoadType.PRIMARY])
        else:
            road_type = random.choice(road_types_pool)

        status = statuses[idx]
        max_speed = speed_lookup[road_type]

        u_point = Point(nodes_dict[u]["longitude"], nodes_dict[u]["latitude"])
        v_point = Point(nodes_dict[v]["longitude"], nodes_dict[v]["latitude"])
        geom = LineString([u_point, v_point])

        graph.add_edge(
            u,
            v,
            source_id=u,
            target_id=v,
            road_type=road_type.value,
            length_km=length_km,
            status=status.value,
            max_speed_kmh=max_speed,
            geometry=geom,
        )

    return graph


def roads_to_geodataframe(graph: nx.Graph) -> gpd.GeoDataFrame:
    """Convert networkx graph edges into a GeoPandas GeoDataFrame with LineString geometries."""
    records = []
    geometries = []

    for u, v, data in graph.edges(data=True):
        records.append({
            "source_id": data["source_id"],
            "target_id": data["target_id"],
            "road_type": data["road_type"],
            "length_km": data["length_km"],
            "status": data["status"],
            "max_speed_kmh": data["max_speed_kmh"],
        })
        geometries.append(data["geometry"])

    gdf = gpd.GeoDataFrame(records, geometry=geometries, crs="EPSG:4326")
    return gdf
