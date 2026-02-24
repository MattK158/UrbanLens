import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import CrimeIncident, IngestionLog
from app.ingestion.client import fetch_incremental

DATASET_ID = "fdj4-gpfu"
DATE_FIELD = "occ_date"

SEVERITY_MAP = {
    "murder": "violent",
    "homicide": "violent",
    "rape": "violent",
    "robbery": "violent",
    "assault": "violent",
    "kidnapping": "violent",
    "burglary": "property",
    "theft": "property",
    "auto theft": "property",
    "arson": "property",
    "vandalism": "property",
}

def get_severity(offense_type: str) -> str:
    if not offense_type:
        return "other"
    offense_lower = offense_type.lower()
    for keyword, severity in SEVERITY_MAP.items():
        if keyword in offense_lower:
            return severity
    return "other"

def get_neighborhood_from_block_group(db: Session, block_group_id: str):
    if not block_group_id:
        return None
    # Austin crime data omits the state FIPS code (48)
    # Our lookup table uses full GEOID format (48 + block_group_id)
    full_id = f"48{block_group_id}"
    result = db.execute(
        text("""
            SELECT neighborhood_id FROM block_group_neighborhood
            WHERE block_group_id = :bg_id
        """),
        {"bg_id": full_id}
    ).fetchone()
    return result[0] if result else None

def ingest_crime(db: Session, since: str = None, max_pages: int = 50):
    print(f"Starting crime ingestion (since={since}, max_pages={max_pages})")

    log = IngestionLog(
        dataset="crime",
        started_at=datetime.now(timezone.utc),
        status="running"
    )
    db.add(log)
    db.commit()

    ingested = 0
    rejected = 0

    try:
        from app.ingestion.client import fetch_dataset
        for page in fetch_dataset(DATASET_ID, order_by=f"{DATE_FIELD} DESC", max_pages=max_pages):
            for record in page:
                try:
                    source_id = record.get("incident_report_number")
                    if not source_id:
                        rejected += 1
                        continue

                    # Check for existing record
                    existing = db.query(CrimeIncident).filter(
                        CrimeIncident.source_id == str(source_id)
                    ).first()
                    if existing:
                        continue

                    # Get neighborhood from block group
                    block_group_id = record.get("census_block_group")
                    neighborhood_id = get_neighborhood_from_block_group(db, block_group_id)

                    # Parse date
                    occurred_at = None
                    date_str = record.get("occ_date")
                    if date_str:
                        try:
                            occurred_at = datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")
                            )
                        except:
                            pass

                    offense_type = record.get("crime_type", "")
                    severity = get_severity(offense_type)

                    incident = CrimeIncident(
                        source_id=str(source_id),
                        offense_type=offense_type,
                        category=record.get("ucr_category", ""),
                        severity=severity,
                        location=None,
                        neighborhood_id=neighborhood_id,
                        occurred_at=occurred_at,
                    )
                    db.add(incident)
                    ingested += 1

                    if ingested % 500 == 0:
                        db.commit()
                        print(f"  Ingested {ingested} crime records...")

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

        print(f"Crime ingestion complete. Ingested: {ingested}, Rejected: {rejected}")
        return ingested, rejected

    except Exception as e:
        log.status = "failed"
        log.completed_at = datetime.now(timezone.utc)
        db.commit()
        print(f"Crime ingestion failed: {e}")
        raise