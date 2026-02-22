import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database import engine, Base
from app.models import *
from dotenv import load_dotenv

load_dotenv()

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")

if __name__ == "__main__":
    init_db()