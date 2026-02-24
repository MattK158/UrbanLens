from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Neighborhood, NeighborhoodScore

router = APIRouter()

@router.get("/scores")
def get_all_scores(db: Session = Depends(get_db)):
    """Returns current UrbanLens scores for all neighborhoods, sorted best to worst."""
    neighborhoods = db.query(Neighborhood).all()
    
    scores = []
    for n in neighborhoods:
        score = db.query(NeighborhoodScore).filter(
            NeighborhoodScore.neighborhood_id == n.id
        ).order_by(NeighborhoodScore.computed_at.desc()).first()

        if score:
            scores.append({
                "neighborhood": n.name,
                "slug": n.slug,
                "overall": float(score.overall_score),
                "safety": float(score.safety_score),
                "infrastructure": float(score.infrastructure_score),
                "emergency_response": float(score.emergency_response_score),
                "development": float(score.development_score),
                "computed_at": score.computed_at.isoformat(),
            })

    scores.sort(key=lambda x: x["overall"], reverse=True)
    return {"scores": scores, "total": len(scores)}


@router.get("/scores/{slug}")
def get_score(slug: str, db: Session = Depends(get_db)):
    """Returns full score breakdown for one neighborhood."""
    n = db.query(Neighborhood).filter(Neighborhood.slug == slug).first()
    if not n:
        raise HTTPException(status_code=404, detail="Neighborhood not found")

    scores = db.query(NeighborhoodScore).filter(
        NeighborhoodScore.neighborhood_id == n.id
    ).order_by(NeighborhoodScore.computed_at.desc()).limit(10).all()

    return {
        "neighborhood": n.name,
        "slug": n.slug,
        "current": {
            "overall": float(scores[0].overall_score) if scores else None,
            "safety": float(scores[0].safety_score) if scores else None,
            "infrastructure": float(scores[0].infrastructure_score) if scores else None,
            "emergency_response": float(scores[0].emergency_response_score) if scores else None,
            "development": float(scores[0].development_score) if scores else None,
            "computed_at": scores[0].computed_at.isoformat() if scores else None,
        },
        "history": [
            {
                "overall": float(s.overall_score),
                "computed_at": s.computed_at.isoformat()
            }
            for s in scores
        ]
    }