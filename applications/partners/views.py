from datetime import datetime, timedelta
from django.shortcuts import render
from django.utils import timezone
from django.http import Http404
from .decorators import partner_required_session
from .services import bookings_for_range, build_halfhour_slots, monthly_summary, partner_fields, week_bounds, weekly_grid

@partner_required_session
def day_calendar_view(request):
    """Calendario del día (vista principal del partner)."""
    tz = timezone.get_current_timezone()
    # día mostrado (query ?date=YYYY-MM-DD) o hoy
    day_str = request.GET.get('date')
    if day_str:
        try:
            day = datetime.strptime(day_str, "%Y-%m-%d").date()
        except ValueError:
            raise Http404("Fecha inválida")
    else:
        day = timezone.localdate()

    start_dt = datetime.combine(day, datetime.min.time()).replace(tzinfo=None)
    end_dt   = start_dt + timedelta(days=1)

    bookings = bookings_for_range(request.gp_user, start_dt, end_dt)
    slots = build_halfhour_slots(day)

    # mapa: para cada slot, si hay overlap con alguna reserva
    slot_data = []
    for s, e in slots:
        # reservas que tocan este slot
        overlaps = [b for b in bookings if (b.start.replace(tzinfo=None) < e and b.end.replace(tzinfo=None) > s)]
        if overlaps:
            b = overlaps[0]
            label = f"Reservado por {b.user.nombre} · {b.field.name}"
            slot_data.append({'start': s, 'end': e, 'status':'busy', 'label': label})
        else:
            slot_data.append({'start': s, 'end': e, 'status':'free', 'label': 'LIBRE'})

    return render(request, 'partners/day.html', {
        'day': day,
        'slot_data': slot_data,
        'fields_count': partner_fields(request.gp_user).count(),
        'prev_date': (day - timedelta(days=1)).strftime("%Y-%m-%d"),
        'next_date': (day + timedelta(days=1)).strftime("%Y-%m-%d"),
        'today': timezone.localdate().strftime("%Y-%m-%d"),
        'section': 'day'
    })

@partner_required_session
def week_calendar_view(request):
    """Stub: calendario semanal (puedes expandir)."""
    # Aquí puedes agrupar por día usando bookings_for_range … (similar a day, pero 7 días)
    return render(request, 'partners/week.html', {'section':'week'})

@partner_required_session
def month_summary_view(request):
    """Resumen mensual (ingresos y conteos)."""
    today = timezone.localdate()
    year  = int(request.GET.get('y', today.year))
    month = int(request.GET.get('m', today.month))
    data  = monthly_summary(request.gp_user, year, month)
    return render(request, 'partners/month.html', {
        'section':'month',
        'year': year, 'month': month, 'summary': data
    })
    
@partner_required_session
def week_calendar_view(request):
    """Calendario semanal sin filtros de template personalizados."""
    monday_str = request.GET.get('monday')
    date_str   = request.GET.get('date')

    if monday_str:
        try:
            monday = datetime.strptime(monday_str, "%Y-%m-%d").date()
        except ValueError:
            raise Http404("Fecha inválida")
    elif date_str:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise Http404("Fecha inválida")
        monday, _ = week_bounds(d)
    else:
        monday, _ = week_bounds(timezone.localdate())

    grid = weekly_grid(request.gp_user, monday, start_hour=8, end_hour=22)

    # Emparejamos cada fila con sus celdas para iterar simple en el template
    rows = grid['rows']          # ej: ["08:00","08:30",...]
    cells = grid['cells']        # matriz: filas × 7
    rows_data = [{'time': rows[i], 'cells': cells[i]} for i in range(len(rows))]

    ctx = {
        'section': 'week',
        'monday': monday,
        'header_days': grid['header_days'],
        'days': grid['days'],
        'prev_monday': grid['prev_monday'],
        'next_monday': grid['next_monday'],
        'this_monday': grid['this_monday'],
        'rows_data': rows_data,   # <- NUEVO
    }
    return render(request, 'partners/week.html', ctx)


