import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.scoring.engine import compute_all_scores

db = SessionLocal()
try:
    compute_all_scores(db)
    print("Done.")
finally:
    db.close()