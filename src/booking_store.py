import sqlite3
import uuid
from datetime import datetime, timedelta

DB_PATH = "bookings.db"

ROOMS = {
    "A": 4,
    "B": 6,
    "C": 8,
    "D": 10,
    "E": 20,
}

SLOT_MINUTES = 30
MAX_DURATION_HOURS = 3


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id TEXT PRIMARY KEY,
                room TEXT NOT NULL,
                title TEXT NOT NULL,
                attendee_count INTEGER NOT NULL,
                start_dt TEXT NOT NULL,
                end_dt TEXT NOT NULL,
                owner TEXT NOT NULL
            )
        """)


def _parse_dt(value: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: {value!r}. Use YYYY-MM-DD HH:MM format.")


def _validate_booking(room: str, attendees: int, start: datetime, end: datetime) -> str | None:
    """Return an error string, or None if valid."""
    if room not in ROOMS:
        return f"Room {room!r} does not exist. Valid rooms: {', '.join(ROOMS)}."
    capacity = ROOMS[room]
    if attendees > capacity:
        return f"Room {room} fits {capacity} people; you requested {attendees}."
    if attendees < 1:
        return "Attendee count must be at least 1."
    if end <= start:
        return "End time must be after start time."
    duration_minutes = (end - start).total_seconds() / 60
    if duration_minutes % SLOT_MINUTES != 0:
        return f"Booking duration must be a multiple of {SLOT_MINUTES} minutes."
    if duration_minutes > MAX_DURATION_HOURS * 60:
        return f"Maximum booking duration is {MAX_DURATION_HOURS} hours."
    if start.minute % SLOT_MINUTES != 0 or start.second != 0:
        return f"Start time must be on a {SLOT_MINUTES}-minute boundary (e.g. 09:00, 09:30)."
    return None


def _has_overlap(conn: sqlite3.Connection, room: str, start: datetime, end: datetime, exclude_id: str | None = None) -> bool:
    query = """
        SELECT 1 FROM bookings
        WHERE room = ?
          AND start_dt < ?
          AND end_dt > ?
    """
    params: list = [room, end.strftime("%Y-%m-%d %H:%M"), start.strftime("%Y-%m-%d %H:%M")]
    if exclude_id:
        query += " AND id != ?"
        params.append(exclude_id)
    row = conn.execute(query, params).fetchone()
    return row is not None


def create_booking(room: str, title: str, attendees: int, start_dt: str, end_dt: str, owner: str) -> dict:
    room = room.upper().strip()
    start = _parse_dt(start_dt)
    end = _parse_dt(end_dt)

    error = _validate_booking(room, attendees, start, end)
    if error:
        return {"success": False, "error": error}

    with _get_conn() as conn:
        if _has_overlap(conn, room, start, end):
            return {"success": False, "error": f"Room {room} is already booked during that time."}
        booking_id = str(uuid.uuid4())[:8]
        conn.execute(
            "INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?)",
            (booking_id, room, title, attendees, start.strftime("%Y-%m-%d %H:%M"), end.strftime("%Y-%m-%d %H:%M"), owner),
        )
    return {"success": True, "booking_id": booking_id, "room": room, "title": title,
            "start": start.strftime("%Y-%m-%d %H:%M"), "end": end.strftime("%Y-%m-%d %H:%M")}


def list_available_rooms(start_dt: str, end_dt: str, attendees: int) -> dict:
    start = _parse_dt(start_dt)
    end = _parse_dt(end_dt)

    if end <= start:
        return {"success": False, "error": "End time must be after start time."}

    duration_minutes = (end - start).total_seconds() / 60
    if duration_minutes % SLOT_MINUTES != 0:
        return {"success": False, "error": f"Duration must be a multiple of {SLOT_MINUTES} minutes."}
    if duration_minutes > MAX_DURATION_HOURS * 60:
        return {"success": False, "error": f"Maximum booking duration is {MAX_DURATION_HOURS} hours."}

    available = []
    with _get_conn() as conn:
        for room, capacity in ROOMS.items():
            if attendees > capacity:
                continue
            if not _has_overlap(conn, room, start, end):
                available.append({"room": room, "capacity": capacity})

    return {"success": True, "available_rooms": available,
            "start": start.strftime("%Y-%m-%d %H:%M"), "end": end.strftime("%Y-%m-%d %H:%M")}


def get_room_schedule(room: str, date: str) -> dict:
    room = room.upper().strip()
    if room not in ROOMS:
        return {"success": False, "error": f"Room {room!r} does not exist. Valid rooms: {', '.join(ROOMS)}."}

    try:
        day = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return {"success": False, "error": f"Cannot parse date {date!r}. Use YYYY-MM-DD format."}

    day_start = datetime.combine(day, datetime.min.time()).replace(hour=0, minute=0)
    day_end = day_start + timedelta(days=1)

    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM bookings WHERE room = ? AND start_dt < ? AND end_dt > ? ORDER BY start_dt",
            (room, day_end.strftime("%Y-%m-%d %H:%M"), day_start.strftime("%Y-%m-%d %H:%M")),
        ).fetchall()

    booked_intervals = [(r["start_dt"], r["end_dt"], r["title"], r["owner"]) for r in rows]

    slots = []
    cursor = day_start.replace(hour=8, minute=0)
    office_end = day_start.replace(hour=20, minute=0)
    while cursor < office_end:
        slot_end = cursor + timedelta(minutes=SLOT_MINUTES)
        occupied_by = None
        for s, e, title, owner in booked_intervals:
            bs = _parse_dt(s)
            be = _parse_dt(e)
            if bs < slot_end and be > cursor:
                occupied_by = {"title": title, "owner": owner}
                break
        slots.append({
            "slot": f"{cursor.strftime('%H:%M')}–{slot_end.strftime('%H:%M')}",
            "status": "occupied" if occupied_by else "available",
            **({"booking": occupied_by} if occupied_by else {}),
        })
        cursor = slot_end

    return {"success": True, "room": room, "date": date, "capacity": ROOMS[room], "slots": slots}


def cancel_booking(booking_id: str, owner: str) -> dict:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        if row is None:
            return {"success": False, "error": f"Booking {booking_id!r} not found."}
        if row["owner"] != owner:
            return {"success": False, "error": "You can only cancel your own bookings."}
        conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    return {"success": True, "cancelled_booking_id": booking_id}


def list_my_bookings(owner: str) -> dict:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM bookings WHERE owner = ? ORDER BY start_dt",
            (owner,),
        ).fetchall()
    bookings = [
        {"id": r["id"], "room": r["room"], "title": r["title"],
         "attendees": r["attendee_count"], "start": r["start_dt"], "end": r["end_dt"]}
        for r in rows
    ]
    return {"success": True, "bookings": bookings}
