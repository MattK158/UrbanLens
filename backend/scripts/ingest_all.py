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

def ingest_all(since: str = None, max_pages: int = 500):
    """
    Runs all four dataset ingestors in sequence.
    Pass since='2024-01-01' for incremental pulls.
    Pass since=None for full historical load (first run only).
    """
    print("=" * 50)
    print("UrbanLens Full Ingestion Pipeline")
    print("=" * 50)

    results = {}
    db = SessionLocal()

    try:
        print("\n[1/4] Crime Incidents")
        ingested, rejected = ingest_crime(db, since=since, max_pages=max_pages)
        results["crime"] = {"ingested": ingested, "rejected": rejected}

        print("\n[2/4] Traffic Incidents")
        ingested, rejected = ingest_traffic(db, since=since, max_pages=max_pages)
        results["traffic"] = {"ingested": ingested, "rejected": rejected}

        print("\n[3/4] Building Permits")
        ingested, rejected = ingest_permits(db, since=since, max_pages=max_pages)
        results["permits"] = {"ingested": ingested, "rejected": rejected}

        print("\n[4/4] Code Complaints")
        ingested, rejected = ingest_code_complaints(db, since=since, max_pages=max_pages)
        results["code_complaints"] = {"ingested": ingested, "rejected": rejected}

    finally:
        db.close()

    print("\n" + "=" * 50)
    print("Ingestion Complete — Summary")
    print("=" * 50)
    total_ingested = 0
    total_rejected = 0
    for dataset, counts in results.items():
        print(f"  {dataset}: {counts['ingested']} ingested, {counts['rejected']} rejected")
        total_ingested += counts["ingested"]
        total_rejected += counts["rejected"]
    print(f"\n  TOTAL: {total_ingested} ingested, {total_rejected} rejected")

    return results

if __name__ == "__main__":
    ingest_all()