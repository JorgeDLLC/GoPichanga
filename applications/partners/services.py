from datetime import datetime, time, timedelta, date
from calendar import day_name
from django.utils import timezone
from django.db.models import Q, Sum, Count
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
