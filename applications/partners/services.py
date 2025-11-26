from datetime import datetime, time, timedelta, date
from calendar import day_name, monthrange
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncDate, ExtractHour
from applications.booking.models import Booking, BookingStatus
from applications.field.models import Field

def partner_fields(user):
    return Field.objects.filter(owner=user)

def bookings_for_range(partner, start_dt, end_dt):
    """Reservas para cualquier cancha del partner en [start_dt, end_dt)."""
    fids = partner_fields(partner).values_list('id', flat=True)
    return (Booking.objects
            .filter(field_id__in=fids,
                    status__in=[BookingStatus.CONFIRMED, BookingStatus.PAID] if hasattr(BookingStatus,'PAID') else [BookingStatus.CONFIRMED],
                    start__lt=end_dt,
                    end__gt=start_dt)
            .select_related('user','field')
            .order_by('start'))

def build_halfhour_slots(day, start_hour=8, end_hour=22):
    """Devuelve lista de (slot_start, slot_end) cada 30 min para el día dado (naive local)."""
    slots = []
    t = datetime.combine(day, time(hour=start_hour))
    end = datetime.combine(day, time(hour=end_hour))
    while t < end:
        slots.append((t, t + timedelta(minutes=30)))
        t += timedelta(minutes=30)
    return slots

def monthly_summary(partner, year, month):
    """Ingresos/estadísticas del mes (naive)."""
    from datetime import date
    from calendar import monthrange
    d0 = datetime(year, month, 1)
    d1 = datetime(year, month, monthrange(year, month)[1], 23, 59, 59)
    qs = bookings_for_range(partner, d0, d1 + timedelta(seconds=1))
    agg = qs.aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    return {
        'total_amount': agg['total'] or 0,
        'count': agg['count'] or 0,
    }


def week_bounds(ref_day: date):
    """Devuelve (monday, sunday_inclusive) como date."""
    # Lunes = 0
    monday = ref_day - timedelta(days=ref_day.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday

def build_week_slots(monday: date, start_hour=8, end_hour=22):
    """
    Devuelve:
      - rows: lista de (slot_start_time, slot_end_time) para cada fila (media hora)
      - days: lista de dates [mon..sun]
    """
    days = [monday + timedelta(days=i) for i in range(7)]
    # filas: usamos el lunes para sacar los cortes horarios (solo importa la hora)
    row_slots = []
    t = datetime.combine(monday, time(hour=start_hour))
    end = datetime.combine(monday, time(hour=end_hour))
    while t < end:
        row_slots.append((t.time(), (t + timedelta(minutes=30)).time()))
        t += timedelta(minutes=30)
    return row_slots, days

def weekly_grid(partner, monday: date, start_hour=8, end_hour=22):
    """
    Construye la grilla semanal:
      - header_days: [{'date': d, 'label': 'Lun 14'} ...]
      - rows: lista de horas ['08:00', '08:30', ...]
      - cells: matriz [len(rows)] x 7, cada celda {'status': 'free'|'busy', 'label': str}
    """
    row_slots, days = build_week_slots(monday, start_hour, end_hour)

    # Rango de consulta
    start_dt = datetime.combine(monday, time(0, 0, 0))
    end_dt   = datetime.combine(days[-1], time(23, 59, 59))
    qs = bookings_for_range(partner, start_dt, end_dt) \
            .select_related('user', 'field')

    # Indexamos por día para chequear overlaps más rápido
    by_day = {d: [] for d in days}
    for b in qs:
        bday = b.start.date()
        # Reservas que tocan varios días (raro en canchas) se reparten
        for d in days:
            if b.start.replace(tzinfo=None) < datetime.combine(d, time(23, 59, 59)) \
               and b.end.replace(tzinfo=None) > datetime.combine(d, time(0, 0, 0)):
                by_day[d].append(b)

    # Armamos celdas
    rows = [f"{rs[0].strftime('%H:%M')}" for rs in row_slots]
    cells = []
    for rs, re in row_slots:
        row_cells = []
        for d in days:
            s = datetime.combine(d, rs)
            e = datetime.combine(d, re)
            overlaps = [b for b in by_day[d] if (b.start.replace(tzinfo=None) < e and b.end.replace(tzinfo=None) > s)]
            if overlaps:
                b = overlaps[0]
                row_cells.append({
                    'status': 'busy',
                    'label': f"{b.user.nombre} · {b.field.name}"
                })
            else:
                row_cells.append({'status': 'free', 'label': 'LIBRE'})
        cells.append(row_cells)

    # Header formateado (Lun/Mar/…)
    day_labels = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
    header_days = [{'date': d, 'label': f"{day_labels[i]} {d.day}"} for i, d in enumerate(days)]

    return {
        'rows': rows,
        'header_days': header_days,
        'days': days,
        'cells': cells,
        'prev_monday': (monday - timedelta(days=7)).strftime("%Y-%m-%d"),
        'next_monday': (monday + timedelta(days=7)).strftime("%Y-%m-%d"),
        'this_monday': week_bounds(timezone.localdate())[0].strftime("%Y-%m-%d"),
    }
    
def _partner_bookings_month(partner, year: int, month: int):
    """QuerySet de reservas del mes para canchas del partner."""
    fields = partner_fields(partner)
    if not fields.exists():
        return Booking.objects.none()

    # rango del mes
    last_day = monthrange(year, month)[1]
    start = datetime(year, month, 1, 0, 0, 0)
    end = datetime(year, month, last_day, 23, 59, 59)

    statuses = [BookingStatus.CONFIRMED]
    if hasattr(BookingStatus, "PAID"):
        statuses.append(BookingStatus.PAID)

    return (
        Booking.objects.filter(
            field__in=fields,
            status__in=statuses,
            start__gte=start,
            start__lte=end,
        )
        .select_related("user", "field")
    )


def monthly_stats(partner, year: int, month: int):
    """
    Calcula métricas para el resumen mensual del partner.
    Devuelve un dict listo para el template.
    """
    qs = _partner_bookings_month(partner, year, month)

    # Ingresos totales
    total_income = qs.aggregate(total=Sum("total_amount"))["total"] or 0

    # Días con más reservas
    days_top = (
        qs.annotate(d=TruncDate("start"))
        .values("d")
        .annotate(c=Count("id"))
        .order_by("-c", "d")[:5]
    )

    # Usuarios más frecuentes
    top_users = (
        qs.values("user__id", "user__nombre")
        .annotate(c=Count("id"))
        .order_by("-c", "user__nombre")[:5]
    )

    # Hora del día más reservada
    hours = (
        qs.annotate(h=ExtractHour("start"))
        .values("h")
        .annotate(c=Count("id"))
        .order_by("-c", "h")
    )
    top_hour = hours[0]["h"] if hours else None

    # Media de reservas por día del mes (sobre días con al menos 1 reserva)
    distinct_days = (
        qs.annotate(d=TruncDate("start"))
        .values("d")
        .distinct()
        .count()
    )
    avg_per_day = (qs.count() / distinct_days) if distinct_days else 0

    # Equipamiento más solicitado (si tienes BookingItem con FK a Equipment)
    # Si aún no lo implementaste, esto quedará vacío sin romper nada.
    try:
        from applications.booking.models import BookingItem  # ajusta nombre real
        top_equipment = (
            BookingItem.objects.filter(booking__in=qs)
            .values("equipment__type")
            .annotate(qty=Sum("quantity"))
            .order_by("-qty")[:5]
        )
    except Exception:
        top_equipment = []

    # Prev / next month helpers
    this_month = date(year, month, 1)
    prev_month = (this_month - timedelta(days=1)).replace(day=1)
    next_month = (this_month + timedelta(days=32)).replace(day=1)

    return {
        "total_income": total_income,
        "days_top": days_top,
        "top_users": top_users,
        "top_equipment": top_equipment,
        "avg_per_day": round(avg_per_day, 2),
        "top_hour": top_hour,
        "prev_year": prev_month.year,
        "prev_month": prev_month.month,
        "next_year": next_month.year,
        "next_month": next_month.month,
    }

def monthly_income_rows(partner, year: int, month: int):
    """
    Devuelve filas de ingresos del mes para el partner:
    [
      {
        "user": "Nombre",
        "start": datetime,
        "end": datetime,
        "hours": 1.5,
        "base_amount": Decimal,
        "extras_amount": Decimal,
        "total": Decimal,
      },
      ...
    ]
    Maneja distintos esquemas de campos sin romper.
    """
    qs = _partner_bookings_month(partner, year, month)

    rows = []
    total_base = 0
    total_extras = 0
    total_total = 0

    # Si existe BookingItem con equipment/extras, intentamos sumar
    try:
        from applications.booking.models import BookingItem
        has_booking_item = True
    except Exception:
        has_booking_item = False

    for b in qs:
        # Duración en horas
        if b.start and b.end:
            seconds = (b.end - b.start).total_seconds()
            hours = round(seconds / 3600, 2)
        else:
            hours = 0

        # Total
        total = getattr(b, "total_amount", None)
        if total is None:
            total = getattr(b, "amount", 0) or 0

        # Extras (si hay campo específico)
        extras = getattr(b, "extras_amount", None)
        if extras is None:
            # Si no hay campo pero existe BookingItem, podríamos calcularlo aquí.
            # Lo dejamos simple: suma de (price * qty) marcados como extra, si tu esquema lo soporta.
            if has_booking_item:
                try:
                    extras = (
                        BookingItem.objects
                        .filter(booking=b, is_extra=True)
                        .aggregate(x=Sum("subtotal"))["x"] or 0
                    )
                except Exception:
                    extras = 0
            else:
                extras = 0

        # Base
        base = total - extras if total is not None else 0

        total_base += base
        total_extras += extras
        total_total += total

        user_name = getattr(b.user, "nombre", None) or getattr(b.user, "email", "") or f"User {b.user_id}"

        rows.append({
            "user": user_name,
            "start": b.start,
            "end": b.end,
            "hours": hours,
            "base_amount": base,
            "extras_amount": extras,
            "total": total,
        })

    # Ordenamos: por fecha
    rows.sort(key=lambda r: (r["start"] or 0))

    return {
        "rows": rows,
        "sum_base": total_base,
        "sum_extras": total_extras,
        "sum_total": total_total,
    }
