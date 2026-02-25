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

@router.get("/trends/{dataset}")
def get_trends(
    dataset: str,
    neighborhood: Optional[str] = Query(None),
    months: int = Query(12),
    db: Session = Depends(get_db)
):
    """Returns monthly aggregated counts for a dataset."""
    if dataset not in DATASET_TABLES:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid dataset")

    table, date_field = DATASET_TABLES[dataset]

    params = {"months": months}
    neighborhood_filter = ""

    if neighborhood:
        from app.models import Neighborhood
        n = db.query(Neighborhood).filter(Neighborhood.slug == neighborhood).first()
        if n:
            neighborhood_filter = "AND neighborhood_id = :nid"
            params["nid"] = n.id

    query = text(f"""
        SELECT 
            EXTRACT(YEAR FROM {date_field}) as year,
            EXTRACT(MONTH FROM {date_field}) as month,
            COUNT(*) as count
        FROM {table}
        WHERE {date_field} >= NOW() - (:months * INTERVAL '1 month')
        {neighborhood_filter}
        GROUP BY year, month
        ORDER BY year, month
    """)

    results = db.execute(query, params).fetchall()

    return {
        "dataset": dataset,
        "neighborhood": neighborhood,
        "data": [
            {
                "year": int(row[0]),
                "month": int(row[1]),
                "count": int(row[2])
            }
            for row in results
        ]
    }