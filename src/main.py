"""Main execution entrypoint for Phase 1 Data Architecture & Dataset Simulation."""
import json
import os
from pathlib import Path

from src.spatial_builder import (
    build_road_graph,
    generate_district_data,
    roads_to_geodataframe,
)
from src.stream_generators import (
    crowdsourced_report_stream_generator,
    load_historical_hazard_logs,
    rainfall_stream_generator,
    river_gauge_stream_generator,
)


def run_pipeline():
    print("=" * 70)
    print("PHASE 1: GEOSPATIAL DATA ARCHITECTURE & SIMULATION PIPELINE")
    print("=" * 70)

    # 1. Generate District Spatial Data
    print("\n[+] Generating District Spatial Topography (10 Settlements)...")
    settlements_gdf = generate_district_data()
    print(f"    -> Generated {len(settlements_gdf)} settlements in Central Himalayan Cluster.")

    # 2. Build Connected Road Network Graph
    print("\n[+] Building Road Network Topology Graph...")
    road_graph = build_road_graph(settlements_gdf)
    roads_gdf = roads_to_geodataframe(road_graph)
    print(f"    -> Nodes: {road_graph.number_of_nodes()}, Edges: {road_graph.number_of_edges()}")

    # 3. Export to GeoJSON
    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)
    settlements_path = output_dir / "settlements.geojson"
    roads_path = output_dir / "roads.geojson"

    settlements_gdf.to_file(settlements_path, driver="GeoJSON")
    roads_gdf.to_file(roads_path, driver="GeoJSON")
    settlements_gdf.to_file("settlements.geojson", driver="GeoJSON")
    roads_gdf.to_file("roads.geojson", driver="GeoJSON")
    print(f"    -> Saved settlements GeoJSON: {settlements_path} & ./settlements.geojson")
    print(f"    -> Saved road network GeoJSON: {roads_path} & ./roads.geojson")

    # 4. Load Historical Hazard Logs
    print("\n[+] Ingesting Historical Hazard Records (25 logs)...")
    historical_logs = load_historical_hazard_logs(25)
    print(f"    -> Ingested {len(historical_logs)} historical hazard events (Provenance: {historical_logs[0].provenance.value})")

    # 5. Run Stream Generators for 5 Ticks
    print("\n[+] Running Streaming Telemetry & Event Generators for 5 Ticks:")
    print("-" * 70)

    settlement_ids = list(settlements_gdf["id"])
    rain_gen = rainfall_stream_generator(settlement_ids)
    river_gen = river_gauge_stream_generator()
    crowd_gen = crowdsourced_report_stream_generator()

    for tick in range(1, 6):
        print(f"\n--- TICK #{tick} ---")
        rain_batch = next(rain_gen)
        river_batch = next(river_gen)
        crowd_report = next(crowd_gen)

        print(f"[*] Rainfall Telemetry ({len(rain_batch)} sensors):")
        for r in rain_batch[:2]:  # Show first 2 for brevity in logs
            print("   ", json.dumps(r.model_dump(mode="json"), indent=2))
        print(f"    ... and {len(rain_batch) - 2} more rain sensor readings.")

        print(f"[*] River Gauges ({len(river_batch)} stations):")
        for g in river_batch:
            print("   ", json.dumps(g.model_dump(mode="json"), indent=2))

        print("[*] Crowdsourced Ground Report:")
        print("   ", json.dumps(crowd_report.model_dump(mode="json"), indent=2))

    print("\n" + "=" * 70)
    print("Simulation execution complete. All records validated and provenance-tagged.")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline()
