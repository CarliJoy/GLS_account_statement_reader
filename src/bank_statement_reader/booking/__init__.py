try:
    from .personal import Booking
except ImportError:
    from .booking_base import BookingBase as Booking

__all__ = ["Booking"]
