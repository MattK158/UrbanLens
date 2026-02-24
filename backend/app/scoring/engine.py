from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import Neighborhood, NeighborhoodScore
from datetime import datetime, timezone

SCORE_VERSION = "1.0"

def percentile_rank(value, all_values):
    """Returns what percentage of values are below this value (0-100)."""
    if not all_values or value is None:
        return 50.0
    below = sum(1 for v in all_values if v < value)
    return (below / len(all_values)) * 100

def compute_all_scores(db: Session):
    """Computes UrbanLens Neighborhood Score for all neighborhoods."""
    print("Computing UrbanLens Neighborhood Scores...")

    neighborhoods = db.query(Neighborhood).all()
    if not neighborhoods:
        print("No neighborhoods found.")
        return

    # Gather raw metrics for all neighborhoods
    raw_metrics = {}

    for n in neighborhoods:
        # Safety: crime density (weighted by severity)
        crime_result = db.execute(text("""
            SELECT
                SUM(CASE WHEN severity = 'violent' THEN 3
                         WHEN severity = 'property' THEN 1
                         ELSE 0.5 END) as weighted_crime
            FROM crime_incidents
            WHERE neighborhood_id = :nid
            AND occurred_at >= NOW() - INTERVAL '12 months'
        """), {"nid": n.id}).fetchone()

        weighted_crime = float(crime_result[0]) if crime_result and crime_result[0] else 0

        # Infrastructure: code complaint density + avg days to close
        complaint_result = db.execute(text("""
            SELECT
                COUNT(*) as complaint_count,
                AVG(EXTRACT(EPOCH FROM (closed_at - opened_at)) / 86400) as avg_days_to_close
            FROM service_requests
            WHERE neighborhood_id = :nid
            AND opened_at >= NOW() - INTERVAL '12 months'
        """), {"nid": n.id}).fetchone()

        complaint_count = float(complaint_result[0]) if complaint_result and complaint_result[0] else 0
        avg_days_to_close = float(complaint_result[1]) if complaint_result and complaint_result[1] else 30

        # Traffic: incident density
        traffic_result = db.execute(text("""
            SELECT COUNT(*) as traffic_count
            FROM traffic_incidents
            WHERE neighborhood_id = :nid
            AND occurred_at >= NOW() - INTERVAL '12 months'
        """), {"nid": n.id}).fetchone()

        traffic_count = float(traffic_result[0]) if traffic_result and traffic_result[0] else 0

        # Development: permit activity (positive signal)
        permit_result = db.execute(text("""
            SELECT COUNT(*) as permit_count
            FROM building_permits
            WHERE neighborhood_id = :nid
            AND issued_at >= NOW() - INTERVAL '12 months'
        """), {"nid": n.id}).fetchone()

        permit_count = float(permit_result[0]) if permit_result and permit_result[0] else 0

        raw_metrics[n.id] = {
            "name": n.name,
            "weighted_crime": weighted_crime,
            "complaint_count": complaint_count,
            "avg_days_to_close": avg_days_to_close,
            "traffic_count": traffic_count,
            "permit_count": permit_count,
        }

    # Extract all values for percentile ranking
    all_crime = [m["weighted_crime"] for m in raw_metrics.values()]
    all_complaints = [m["complaint_count"] for m in raw_metrics.values()]
    all_days = [m["avg_days_to_close"] for m in raw_metrics.values()]
    all_traffic = [m["traffic_count"] for m in raw_metrics.values()]
    all_permits = [m["permit_count"] for m in raw_metrics.values()]

    # Compute scores for each neighborhood
    computed_at = datetime.now(timezone.utc)

    for n in neighborhoods:
        m = raw_metrics[n.id]

        # Safety score (lower crime = higher score)
        safety_score = 100 - percentile_rank(m["weighted_crime"], all_crime)

        # Infrastructure score (lower complaints + faster resolution = higher score)
        raw_infra = (
            percentile_rank(m["complaint_count"], all_complaints) * 0.6 +
            percentile_rank(m["avg_days_to_close"], all_days) * 0.4
        )
        infrastructure_score = 100 - raw_infra

        # Traffic score (lower traffic incidents = higher score)
        emergency_response_score = 100 - percentile_rank(m["traffic_count"], all_traffic)

        # Development score (higher permits = higher score, positive signal)
        development_score = percentile_rank(m["permit_count"], all_permits)

        # Overall weighted score
        overall_score = (
            safety_score * 0.40 +
            infrastructure_score * 0.25 +
            emergency_response_score * 0.20 +
            development_score * 0.15
        )

        score = NeighborhoodScore(
            neighborhood_id=n.id,
            computed_at=computed_at,
            overall_score=round(overall_score, 2),
            safety_score=round(safety_score, 2),
            infrastructure_score=round(infrastructure_score, 2),
            emergency_response_score=round(emergency_response_score, 2),
            development_score=round(development_score, 2),
            score_version=SCORE_VERSION,
        )
        db.add(score)

    db.commit()
    print(f"Scores computed for {len(neighborhoods)} neighborhoods.")