import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import httpx
import geopandas as gpd
import pandas as pd
from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models import Neighborhood
from dotenv import load_dotenv

load_dotenv()

# Census Bureau Texas block group boundaries
CENSUS_URL = "https://www2.census.gov/geo/tiger/TIGER2023/BG/tl_2023_48_bg.zip"

def build_lookup():
    print("Downloading Texas census block group boundaries...")
    
    # Download and read the census shapefile
    gdf_blocks = gpd.read_file(CENSUS_URL)
    print(f"Downloaded {len(gdf_blocks)} Texas block groups")

    # Filter to Austin area bounding box
    austin_bbox = (-97.928, 30.098, -97.562, 30.516)
    gdf_blocks = gdf_blocks.cx[austin_bbox[0]:austin_bbox[2], austin_bbox[1]:austin_bbox[3]]
    print(f"Filtered to {len(gdf_blocks)} Austin area block groups")

    # Ensure CRS matches (WGS84)
    gdf_blocks = gdf_blocks.to_crs("EPSG:4326")

    # Load neighborhood boundaries from database
    print("Loading neighborhood boundaries from database...")
    db = SessionLocal()
    
    try:
        neighborhoods = db.query(Neighborhood).all()
        print(f"Loaded {len(neighborhoods)} neighborhoods")

        # Create lookup table in database
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS block_group_neighborhood (
                    block_group_id VARCHAR(20) PRIMARY KEY,
                    neighborhood_id INTEGER REFERENCES neighborhoods(id),
                    neighborhood_name VARCHAR(100)
                )
            """))
            conn.execute(text("TRUNCATE block_group_neighborhood"))
            conn.commit()

        print("Mapping block groups to neighborhoods...")
        matched = 0
        unmatched = 0

        for _, block in gdf_blocks.iterrows():
            block_id = block.get("GEOID", "")
            if not block_id:
                continue

            # Get centroid of block group
            centroid = block.geometry.centroid
            lon, lat = centroid.x, centroid.y

            # Find which neighborhood contains this centroid
            result = db.execute(
                text("""
                    SELECT id, name FROM neighborhoods
                    WHERE ST_Contains(
                        boundary,
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
                    )
                    LIMIT 1
                """),
                {"lat": lat, "lon": lon}
            ).fetchone()

            if result:
                with engine.connect() as conn:
                    conn.execute(
                        text("""
                            INSERT INTO block_group_neighborhood 
                            (block_group_id, neighborhood_id, neighborhood_name)
                            VALUES (:bg_id, :n_id, :n_name)
                            ON CONFLICT (block_group_id) DO NOTHING
                        """),
                        {"bg_id": block_id, "n_id": result[0], "n_name": result[1]}
                    )
                    conn.commit()
                matched += 1
            else:
                unmatched += 1

        print(f"\nDone. Matched: {matched}, Unmatched: {unmatched}")

    finally:
        db.close()

if __name__ == "__main__":
    build_lookup()