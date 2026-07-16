from langchain_core.tools import tool
from src import booking_store


def make_tools(current_user: str) -> list:
    """Return tool instances bound to the logged-in user."""

    @tool
    def create_booking(room: str, title: str, attendees: int, start_dt: str, end_dt: str) -> dict:
        """Book a meeting room for the current user.

        Args:
            room: Room letter — one of A, B, C, D, E.
            title: A short title for the meeting (e.g. "Interview with Jane").
            attendees: Number of people attending (must not exceed room capacity).
            start_dt: Start datetime in YYYY-MM-DD HH:MM format (must be on a 30-min boundary).
            end_dt: End datetime in YYYY-MM-DD HH:MM format (max 3 hours after start).
        """
        return booking_store.create_booking(room, title, attendees, start_dt, end_dt, current_user)

    @tool
    def list_available_rooms(start_dt: str, end_dt: str, attendees: int) -> dict:
        """List all rooms that are free and large enough for a given time range.

        Args:
            start_dt: Start datetime in YYYY-MM-DD HH:MM format.
            end_dt: End datetime in YYYY-MM-DD HH:MM format.
            attendees: Number of people who will attend.
        """
        return booking_store.list_available_rooms(start_dt, end_dt, attendees)

    @tool
    def get_room_schedule(room: str, date: str) -> dict:
        """Show the full daily schedule for a room — every 30-min slot marked available or occupied.

        Args:
            room: Room letter — one of A, B, C, D, E.
            date: Date in YYYY-MM-DD format.
        """
        return booking_store.get_room_schedule(room, date)

    @tool
    def cancel_booking(booking_id: str) -> dict:
        """Cancel one of the current user's bookings.

        Args:
            booking_id: The booking ID returned when the booking was created.
        """
        return booking_store.cancel_booking(booking_id, current_user)

    @tool
    def list_my_bookings() -> dict:
        """List all upcoming and past bookings belonging to the current user."""
        return booking_store.list_my_bookings(current_user)

    return [create_booking, list_available_rooms, get_room_schedule, cancel_booking, list_my_bookings]
