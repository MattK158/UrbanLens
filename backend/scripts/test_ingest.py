import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.ingestion.crime import ingest_crime
from app.ingestion.traffic import ingest_traffic
from app.ingestion.permits import ingest_permits
from app.ingestion.code_complaints import ingest_code_complaints

db = SessionLocal()
try:
    print("[1/4] Crime Incidents")
    ingest_crime(db, max_pages=500)

    print("\n[2/4] Traffic Incidents")
    ingest_traffic(db, max_pages=500)

    print("\n[3/4] Building Permits")
    ingest_permits(db, max_pages=500)

    print("\n[4/4] Code Complaints")
    ingest_code_complaints(db, max_pages=500)
finally:
    db.close()