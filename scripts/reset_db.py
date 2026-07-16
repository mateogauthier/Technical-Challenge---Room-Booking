"""Delete and recreate the bookings database. Run before demos or tests."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import sqlite3
from src.booking_store import DB_PATH, init_db

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"Deleted {DB_PATH}")

init_db()
print(f"Fresh database created at {DB_PATH}")
