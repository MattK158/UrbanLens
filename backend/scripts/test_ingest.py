import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.ingestion.crime import ingest_crime
from app.ingestion.traffic import ingest_traffic
from app.ingestion.permits import ingest_permits
from app.ingestion.code_complaints import ingest_code_complaints
from dotenv import load_dotenv

load_dotenv()

db = SessionLocal()
try:
    print("=== CRIME ===")
    ingest_crime(db, max_pages=2)

    print("\n=== TRAFFIC ===")
    ingest_traffic(db, max_pages=2)

    print("\n=== PERMITS ===")
    ingest_permits(db, max_pages=2)

    print("\n=== CODE COMPLAINTS ===")
    ingest_code_complaints(db, max_pages=2)

    print("\nTest ingestion complete.")
finally:
    db.close()