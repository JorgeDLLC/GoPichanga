from applications.booking.models import Booking
from django.utils import timezone

def user_bookings(user):
    """Devuelve todas las reservas del usuario autenticado."""
    return (
        Booking.objects
        .filter(user=user)
        .select_related("field", "field__owner")
        .order_by("-start")
    )
