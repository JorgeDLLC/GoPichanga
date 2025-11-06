# applications/payments/services.py
from decimal import Decimal
from django.db import transaction
from applications.payments.models import Payment, PaymentStatus
from applications.booking.models import Booking, BookingExtra, BookingStatus
from applications.booking.services import field_is_free, equipment_available_qty

def compute_total(field_price_hour: Decimal, start, end, extras: list[dict]) -> Decimal:
    hours = Decimal((end - start).total_seconds()) / Decimal(3600)
    base = (field_price_hour or Decimal('0')) * hours
    extras_total = sum(Decimal(e['quantity']) * Decimal(e['unit_price']) for e in extras)
    return base + extras_total

@transaction.atomic
def confirm_payment_and_create_booking(*, user, field, start, end, extras, form):
    """
    - Revalida disponibilidad del campo y de los extras
    - Crea Booking + BookingExtra
    - Crea Payment simulado aprobado
    - Devuelve (booking, payment)
    """
    from applications.field.models import FieldEquipment  # import local para evitar ciclos

    if not field_is_free(field, start, end):
        raise ValueError("El campo ya está reservado en ese horario.")

    # validar stock
    for e in extras:
        fe: FieldEquipment = e['fe']
        qty: int = e['quantity']
        disp = equipment_available_qty(fe, start, end)
        if qty > disp:
            raise ValueError(f"Stock insuficiente de {fe.equipment.get_type_display()} (disp {disp}).")

    # total
    total = compute_total(field.price_hour, start, end, [
        {'quantity': e['quantity'], 'unit_price': e['unit_price']} for e in extras
    ])

    # crear booking
    booking = Booking.objects.create(
        user=user, field=field, start=start, end=end,
        status=BookingStatus.CONFIRMED, total_amount=total
    )

    # extras
    for e in extras:
        BookingExtra.objects.create(
            booking=booking,
            field_equipment=e['fe'],
            quantity=e['quantity'],
            unit_price=e['unit_price']
        )

    # payment simulado
    payment = Payment.objects.create(
        booking=booking,
        status=PaymentStatus.APPROVED,
        amount=total,
        holder_name=form.cleaned_data['holder_name'],
        card_brand=form.card_brand(),
        last4=form.card_last4(),
        auth_code='AP-' + str(booking.id).zfill(6),
    )

    return booking, payment, total
