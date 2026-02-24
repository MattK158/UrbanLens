from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from typing import Optional

router = APIRouter()

DATASET_TABLES = {
    "crime": ("crime_incidents", "occurred_at"),
    "traffic": ("traffic_incidents", "occurred_at"),
    "permits": ("building_permits", "issued_at"),
    "code_complaints": ("service_requests", "opened_at"),
}

@router.get("/map/{dataset}")
def get_map_data(
    dataset: str,
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Returns GeoJSON point data for a dataset within date range and bounding box."""
    if dataset not in DATASET_TABLES:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid dataset. Choose from: {list(DATASET_TABLES.keys())}")

    table, date_field = DATASET_TABLES[dataset]

    # Build query
    where_clauses = ["location IS NOT NULL"]
    params = {}

    if start:
        where_clauses.append(f"{date_field} >= :start")
        params["start"] = start

    if end:
        where_clauses.append(f"{date_field} <= :end")
        params["end"] = end

    if bbox:
        try:
            west, south, east, north = map(float, bbox.split(","))
            where_clauses.append("""
                ST_Within(location, ST_MakeEnvelope(:west, :south, :east, :north, 4326))
            """)
            params.update({"west": west, "south": south, "east": east, "north": north})
        except:
            pass

    where_sql = " AND ".join(where_clauses)

    # Extra fields per dataset
    extra_fields = {
        "crime": ", offense_type, severity",
        "traffic": ", incident_type",
        "permits": ", permit_type, permit_value",
        "code_complaints": ", complaint_type, status",
    }

    extra = extra_fields.get(dataset, "")

    query = text(f"""
        SELECT 
            id,
            ST_X(location::geometry) as lon,
            ST_Y(location::geometry) as lat,
            neighborhood_id
            {extra}
        FROM {table}
        WHERE {where_sql}
        LIMIT 10000
    """)

    results = db.execute(query, params).fetchall()

    features = []
    for row in results:
        props = {"id": row[0], "neighborhood_id": row[3]}
        
        if dataset == "crime":
            props["offense_type"] = row[4]
            props["severity"] = row[5]
        elif dataset == "traffic":
            props["incident_type"] = row[4]
        elif dataset == "permits":
            props["permit_type"] = row[4]
            props["permit_value"] = float(row[5]) if row[5] else None
        elif dataset == "code_complaints":
            props["complaint_type"] = row[4]
            props["status"] = row[5]

        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row[1], row[2]]},
            "properties": props
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "count": len(features)
    }