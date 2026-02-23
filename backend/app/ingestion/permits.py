from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import BuildingPermit, IngestionLog
from app.ingestion.client import fetch_incremental

DATASET_ID = "3syk-w9eu"
DATE_FIELD = "issue_date"

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

def ingest_permits(db: Session, since: str = None, max_pages: int = 50):
    print(f"Starting permits ingestion (since={since}, max_pages={max_pages})")

    log = IngestionLog(
        dataset="permits",
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
                    source_id = record.get("permit_number")
                    lat = record.get("latitude")
                    lon = record.get("longitude")

                    if not source_id or not lat or not lon:
                        rejected += 1
                        continue

                    lat, lon = float(lat), float(lon)

                    if not (30.098 <= lat <= 30.516 and -97.928 <= lon <= -97.562):
                        rejected += 1
                        continue

                    existing = db.query(BuildingPermit).filter(
                        BuildingPermit.source_id == str(source_id)
                    ).first()
                    if existing:
                        continue

                    issued_at = None
                    date_str = record.get("issue_date")
                    if date_str:
                        try:
                            issued_at = datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")
                            )
                        except:
                            pass

                    permit_value = None
                    val = record.get("total_valuation") or record.get("permit_value")
                    if val:
                        try:
                            permit_value = float(str(val).replace(",", ""))
                        except:
                            pass

                    neighborhood_id = get_neighborhood_id(db, lat, lon)

                    permit = BuildingPermit(
                        source_id=str(source_id),
                        permit_type=record.get("permittype", ""),
                        work_type=record.get("work_class", ""),
                        location=f"SRID=4326;POINT({lon} {lat})",
                        neighborhood_id=neighborhood_id,
                        issued_at=issued_at,
                        permit_value=permit_value,
                    )
                    db.add(permit)
                    ingested += 1

                    if ingested % 500 == 0:
                        db.commit()
                        print(f"  Ingested {ingested} permit records...")

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

        print(f"Permits ingestion complete. Ingested: {ingested}, Rejected: {rejected}")
        return ingested, rejected

    except Exception as e:
        log.status = "failed"
        log.completed_at = datetime.now(timezone.utc)
        db.commit()
        print(f"Permits ingestion failed: {e}")
        raise