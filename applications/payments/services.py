# applications/payments/services.py
from decimal import Decimal
from django.db import transaction
from applications.booking.models import Booking, BookingExtra, BookingStatus


def compute_total(price_hour, start, end, extras):
    """Calcula total = horas * precio + extras."""
    duration_hours = (end - start).total_seconds() / 3600
    if duration_hours <= 0:
        raise ValueError("La hora de fin debe ser posterior a la hora de inicio.")

    base = Decimal(price_hour) * Decimal(duration_hours)

    extras_total = sum(
        Decimal(e["quantity"]) * Decimal(e["unit_price"]) for e in extras
    )

    return base + extras_total


@transaction.atomic
def confirm_payment_and_create_booking(*, user, field, start, end, extras, form):
    """Crea la reserva + extras (pago simulado)."""

    print(">> confirm_payment_and_create_booking")  # DEBUG
    print("   user:", user.id, "field:", field.id)
    print("   start/end:", start, end)
    print("   extras len:", len(extras))
    overlap = Booking.objects.filter(
        field=field,
        status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
        start__lt=end,
        end__gt=start,
    ).exists()
    print("   overlap?", overlap)  # DEBUG
    if overlap:
        raise ValueError("La cancha ya tiene una reserva en ese horario.")

    # 2) Total
    total = compute_total(field.price_hour, start, end, [
        {"quantity": e["quantity"], "unit_price": e["unit_price"]} for e in extras
    ])
    print("   computed total:", total)  # DEBUG
    # 3) Booking
    booking = Booking.objects.create(
        user=user,
        field=field,
        start=start,
        end=end,
        status=BookingStatus.CONFIRMED,
        total_amount=total,
    )
    print("   booking saved id:", booking.id)  # DEBUG
    
    # 4) Extras
    for e in extras:
        BookingExtra.objects.create(
            booking=booking,
            field_equipment=e["fe"],
            quantity=e["quantity"],
            unit_price=e["unit_price"],
        )
    print("   extras saved")  # DEBUG
    # 5) Pago simulado
    payment = None
    payment_info = {
        "brand": form.card_brand(),
        "last4": form.card_last4(),
        "amount": total,
    }
    return booking, payment, payment_info
