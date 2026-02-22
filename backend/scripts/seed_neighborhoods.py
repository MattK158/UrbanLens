import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import requests
import json
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import Neighborhood
from dotenv import load_dotenv
import re

load_dotenv()

# Austin neighborhood boundaries from the city's open data portal
NEIGHBORHOODS_URL = "https://data.austintexas.gov/resource/inrm-c3ee.geojson?$limit=200"

def slugify(name):
    name = name.lower()
    name = re.sub(r'[^a-z0-9\s-]', '', name)
    name = re.sub(r'[\s]+', '-', name)
    return name.strip('-')

def seed_neighborhoods():
    print("Fetching Austin neighborhood boundaries...")
    
    response = requests.get(NEIGHBORHOODS_URL, timeout=30)
    if response.status_code != 200:
        print(f"Failed to fetch neighborhoods: {response.status_code}")
        sys.exit(1)
    
    data = response.json()
    features = data.get("features", [])
    print(f"Found {len(features)} neighborhoods")

    db = SessionLocal()
    
    try:
        count = 0
        skipped = 0
        
        seen_slugs = set()

        for feature in features:
            props = feature.get("properties", {})
            geometry = feature.get("geometry", {})

            name = (
                props.get("planning_area_name") or
                props.get("neighname") or
                props.get("name")
            )

            if not name or not geometry:
                skipped += 1
                continue

            name = name.strip().title()
            slug = slugify(name)

            # Skip duplicates within this batch
            if slug in seen_slugs:
                skipped += 1
                continue
            seen_slugs.add(slug)

            # Check if already exists in DB
            existing = db.query(Neighborhood).filter(
                Neighborhood.slug == slug
            ).first()

            if existing:
                skipped += 1
                continue

            geom_type = geometry.get("type", "")
            coordinates = geometry.get("coordinates", [])

            if geom_type == "Polygon":
                wkt = polygon_to_wkt(coordinates)
                wkt = f"MULTIPOLYGON(({wkt[8:-1]}))"
            elif geom_type == "MultiPolygon":
                wkt = multipolygon_to_wkt(coordinates)
            else:
                skipped += 1
                continue

            neighborhood = Neighborhood(
                name=name,
                slug=slug,
                boundary=f"SRID=4326;{wkt}",
            )

            db.add(neighborhood)
            count += 1

            if count % 10 == 0:
                db.commit()
                print(f"  Inserted {count} neighborhoods...")

        db.commit()
        print(f"\nDone. Inserted {count} neighborhoods, skipped {skipped}.")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


def polygon_to_wkt(coordinates):
    rings = []
    for ring in coordinates:
        points = ", ".join(f"{lon} {lat}" for lon, lat in ring)
        rings.append(f"({points})")
    return f"POLYGON({', '.join(rings)})"


def multipolygon_to_wkt(coordinates):
    polygons = []
    for polygon in coordinates:
        rings = []
        for ring in polygon:
            points = ", ".join(f"{lon} {lat}" for lon, lat in ring)
            rings.append(f"({points})")
        polygons.append(f"({', '.join(rings)})")
    return f"MULTIPOLYGON({', '.join(polygons)})"


if __name__ == "__main__":
    seed_neighborhoods()