from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import TrafficIncident, IngestionLog
from app.ingestion.client import fetch_incremental

DATASET_ID = "r3af-2r8x"
DATE_FIELD = "published_date"

def get_neighborhood_id(db: Session, lat: float, lon: float):
    result = db.execute(
        text("""
            SELECT id FROM neighborhoods
            WHERE ST_Contains(boundary, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
            LIMIT 1
        """),
        {"lat": lat, "lon": lon}
    ).fetchone()
    return result[0] if result else None

def ingest_traffic(db: Session, since: str = None, max_pages: int = 50):
    print(f"Starting traffic ingestion (since={since}, max_pages={max_pages})")

    log = IngestionLog(
        dataset="traffic",
        started_at=datetime.now(timezone.utc),
        status="running"
    )
    db.add(log)
    db.commit()

    ingested = 0
    rejected = 0

    try:
        for page in fetch_incremental(DATASET_ID, DATE_FIELD, since=since):
            for record in page:
                try:
                    source_id = record.get("traffic_report_id")
                    lat = record.get("latitude")
                    lon = record.get("longitude")

                    if not source_id or not lat or not lon:
                        rejected += 1
                        continue

                    lat, lon = float(lat), float(lon)

                    if not (30.098 <= lat <= 30.516 and -97.928 <= lon <= -97.562):
                        rejected += 1
                        continue

                    existing = db.query(TrafficIncident).filter(
                        TrafficIncident.source_id == str(source_id)
                    ).first()
                    if existing:
                        continue

                    occurred_at = None
                    date_str = record.get("published_date")
                    if date_str:
                        try:
                            occurred_at = datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")
                            )
                        except:
                            pass

                    neighborhood_id = get_neighborhood_id(db, lat, lon)

                    incident = TrafficIncident(
                        source_id=str(source_id),
                        incident_type=record.get("issue_reported", ""),
                        location=f"SRID=4326;POINT({lon} {lat})",
                        neighborhood_id=neighborhood_id,
                        occurred_at=occurred_at,
                    )
                    db.add(incident)
                    ingested += 1

                    if ingested % 500 == 0:
                        db.commit()
                        print(f"  Ingested {ingested} traffic records...")

                except Exception as e:
                    rejected += 1
                    continue

            db.commit()

        log.status = "success"
        log.completed_at = datetime.now(timezone.utc)
        log.records_ingested = ingested
        log.records_rejected = rejected
        log.last_ingested_at = datetime.now(timezone.utc)
        db.commit()

        print(f"Traffic ingestion complete. Ingested: {ingested}, Rejected: {rejected}")
        return ingested, rejected

    except Exception as e:
        log.status = "failed"
        log.completed_at = datetime.now(timezone.utc)
        db.commit()
        print(f"Traffic ingestion failed: {e}")
        raise