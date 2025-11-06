from dataclasses import dataclass
from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from .models import Booking, BookingExtra, BookingStatus
from .exceptions import BookingError, SlotNotAvailable, ExtraOutOfStock
from .services import field_is_free, equipment_available_qty, compute_total
from applications.field.models import Field, FieldEquipment
from applications.users.models import User

@dataclass(frozen=True)
class ExtraRequest:
    fe_id: int
    quantity: int

class BookingFactory:
    @staticmethod
    def create(*, user: User, field: Field, start, end, extras: list[ExtraRequest]) -> Booking:
        if start >= end:
            raise BookingError("La hora fin debe ser posterior a la hora inicio.")

        # Normaliza a timezone-aware si trabajas así en el proyecto
        if timezone.is_naive(start):
            start = timezone.make_aware(start, timezone.get_current_timezone())
        if timezone.is_naive(end):
            end = timezone.make_aware(end, timezone.get_current_timezone())

        # 1) Campo libre
        if not field_is_free(field, start, end):
            raise SlotNotAvailable("El campo ya está reservado en ese horario.")

        # 2) Carga los extras solicitados (solo los ids pedidos y del mismo field)
        ids = [e.fe_id for e in extras if e.quantity and e.quantity > 0]
        fe_map = {fe.id: fe for fe in FieldEquipment.objects.filter(field=field, id__in=ids).select_related('equipment')}

        # 3) Validación de stock por cada extra
        extra_payload = []
        for req in extras:
            if req.quantity <= 0:
                continue
            fe = fe_map.get(req.fe_id)
            if not fe:
                raise BookingError("Extra inválido para esta cancha.")
            available = equipment_available_qty(fe, start, end)
            if req.quantity > available:
                raise ExtraOutOfStock(
                    f"No hay suficiente stock de {fe.equipment.get_type_display()} (disponible {available})."
                )
            extra_payload.append({
                "fe": fe,
                "quantity": req.quantity,
                "unit_price": fe.price_per_unit,
            })

        # 4) Total
        hours = Decimal((end - start) / timedelta(hours=1))
        total = compute_total(field.price_hour, hours, [
            {"quantity": e["quantity"], "unit_price": e["unit_price"]} for e in extra_payload
        ])

        # 5) Persistencia atómica
        with transaction.atomic():
            booking = Booking.objects.create(
                user=user,
                field=field,
                start=start,
                end=end,
                status=BookingStatus.PENDING,
                total_amount=total,
            )
            for e in extra_payload:
                BookingExtra.objects.create(
                    booking=booking,
                    field_equipment=e["fe"],
                    quantity=e["quantity"],
                    unit_price=e["unit_price"],
                )
        return booking
