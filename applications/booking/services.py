from decimal import Decimal
from django.db.models import Sum
from .models import Booking, BookingStatus, BookingExtra
from applications.field.models import FieldEquipment

def field_is_free(field, start, end) -> bool:
    """No hay solape si NO existe una reserva (pend/confirm) que cumpla: start < end AND end > start."""
    return not Booking.objects.filter(
        field=field,
        status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
        start__lt=end,
        end__gt=start,
    ).exists()

def equipment_available_qty(field_equipment: FieldEquipment, start, end) -> int:
    """Stock disponible del extra (stock físico - cantidad ya reservada en el mismo rango)."""
    reserved = BookingExtra.objects.filter(
        field_equipment=field_equipment,
        booking__status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
        booking__start__lt=end,
        booking__end__gt=start,
    ).aggregate(q=Sum('quantity'))['q'] or 0
    return max(0, field_equipment.stock - reserved)

def compute_total(field_price_hour: Decimal, hours: Decimal, extras: list[dict]) -> Decimal:
    base = field_price_hour * hours
    extras_total = sum(Decimal(e['quantity']) * Decimal(e['unit_price']) for e in extras)
    return base + extras_total
