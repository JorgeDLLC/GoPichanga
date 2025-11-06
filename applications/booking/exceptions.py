class BookingError(Exception):
    """Base domain error for bookings."""


class SlotNotAvailable(BookingError):
    """The field is not free for the requested time slot."""


class ExtraOutOfStock(BookingError):
    """Requested quantity exceeds available stock for an extra."""
