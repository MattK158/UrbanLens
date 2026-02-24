from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import Neighborhood, NeighborhoodScore
from functools import lru_cache
import json

router = APIRouter()
_neighborhoods_cache = None
_cache_time = None

@router.get("/neighborhoods")
def get_all_neighborhoods(db: Session = Depends(get_db)):
    global _neighborhoods_cache, _cache_time
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    if _neighborhoods_cache and _cache_time and (now - _cache_time) < timedelta(hours=1):
        return _neighborhoods_cache
    
    """Returns all neighborhoods with boundaries as GeoJSON and current scores."""
    neighborhoods = db.query(Neighborhood).all()
    
    features = []
    for n in neighborhoods:
        # Get latest score
        score = db.query(NeighborhoodScore).filter(
            NeighborhoodScore.neighborhood_id == n.id
        ).order_by(NeighborhoodScore.computed_at.desc()).first()

        # Get boundary as GeoJSON
        result = db.execute(
            text("SELECT ST_AsGeoJSON(boundary) FROM neighborhoods WHERE id = :id"),
            {"id": n.id}
        ).fetchone()
        
        geometry = None
        if result and result[0]:
            import json
            geometry = json.loads(result[0])

        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "id": n.id,
                "name": n.name,
                "slug": n.slug,
                "overall_score": float(score.overall_score) if score else None,
            }
        })

    result = {"type": "FeatureCollection", "features": features}
    _neighborhoods_cache = result
    _cache_time = datetime.now(timezone.utc)
    return result


@router.get("/neighborhoods/{slug}")
def get_neighborhood(slug: str, db: Session = Depends(get_db)):
    """Returns full detail for one neighborhood."""
    n = db.query(Neighborhood).filter(Neighborhood.slug == slug).first()
    if not n:
        raise HTTPException(status_code=404, detail="Neighborhood not found")

    # Get latest score
    score = db.query(NeighborhoodScore).filter(
        NeighborhoodScore.neighborhood_id == n.id
    ).order_by(NeighborhoodScore.computed_at.desc()).first()

    # Get crime count (90 days)
    crime_count = db.execute(
        text("""
            SELECT COUNT(*) FROM crime_incidents
            WHERE neighborhood_id = :nid
            AND occurred_at >= NOW() - INTERVAL '90 days'
        """),
        {"nid": n.id}
    ).scalar()

    # Get traffic count (90 days)
    traffic_count = db.execute(
        text("""
            SELECT COUNT(*) FROM traffic_incidents
            WHERE neighborhood_id = :nid
            AND occurred_at >= NOW() - INTERVAL '90 days'
        """),
        {"nid": n.id}
    ).scalar()

    # Get permit count (90 days)
    permit_count = db.execute(
        text("""
            SELECT COUNT(*) FROM building_permits
            WHERE neighborhood_id = :nid
            AND issued_at >= NOW() - INTERVAL '90 days'
        """),
        {"nid": n.id}
    ).scalar()

    # Get code complaints count (90 days)
    complaint_count = db.execute(
        text("""
            SELECT COUNT(*) FROM service_requests
            WHERE neighborhood_id = :nid
            AND opened_at >= NOW() - INTERVAL '90 days'
        """),
        {"nid": n.id}
    ).scalar()

    # Get neighborhood rank
    rank_result = db.execute(
        text("""
            SELECT COUNT(*) FROM neighborhood_scores ns
            JOIN (
                SELECT neighborhood_id, MAX(computed_at) as max_date
                FROM neighborhood_scores
                GROUP BY neighborhood_id
            ) latest ON ns.neighborhood_id = latest.neighborhood_id 
                AND ns.computed_at = latest.max_date
            WHERE ns.overall_score > (
                SELECT COALESCE(overall_score, 0) FROM neighborhood_scores
                WHERE neighborhood_id = :nid
                ORDER BY computed_at DESC LIMIT 1
            )
        """),
        {"nid": n.id}
    ).scalar()

    total_neighborhoods = db.query(Neighborhood).count()

    return {
        "id": n.id,
        "name": n.name,
        "slug": n.slug,
        "scores": {
            "overall": float(score.overall_score) if score else None,
            "safety": float(score.safety_score) if score else None,
            "infrastructure": float(score.infrastructure_score) if score else None,
            "emergency_response": float(score.emergency_response_score) if score else None,
            "development": float(score.development_score) if score else None,
            "computed_at": score.computed_at.isoformat() if score else None,
        },
        "stats": {
            "crime_incidents_90d": crime_count,
            "traffic_incidents_90d": traffic_count,
            "permits_90d": permit_count,
            "code_complaints_90d": complaint_count,
        },
        "rank": {
            "overall": int(rank_result) + 1 if rank_result is not None else None,
            "of": total_neighborhoods
        }
    }


@router.get("/neighborhoods/{slug}/compare/{slug2}")
def compare_neighborhoods(slug: str, slug2: str, db: Session = Depends(get_db)):
    """Returns side by side comparison of two neighborhoods."""
    n1 = get_neighborhood(slug, db)
    n2 = get_neighborhood(slug2, db)
    return {"neighborhood_1": n1, "neighborhood_2": n2}