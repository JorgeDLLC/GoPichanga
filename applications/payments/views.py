from datetime import datetime
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.contrib import messages
from applications.users.utils import login_required_session
from applications.users.models import User
from applications.field.models import Field, FieldEquipment
from .forms import PaymentForm
from .services import confirm_payment_and_create_booking, compute_total

@login_required_session
def checkout_view(request, field_id):
    field = get_object_or_404(Field, pk=field_id)
    user  = get_object_or_404(User, pk=request.session.get('user_id'))

    data = request.POST if request.method == 'POST' else request.GET
    try:
        start = datetime.strptime(f"{data.get('date')} {data.get('start_time')}", "%Y-%m-%d %H:%M")
        end   = datetime.strptime(f"{data.get('end_time')}", "%H:%M").replace(
            year=start.year, month=start.month, day=start.day
        )
    except Exception:
        messages.error(request, "Debes proporcionar fecha y horas válidas.")
        return redirect(reverse('field:list'))

    # extras solicitados
    fe_list = list(FieldEquipment.objects.filter(field=field).select_related('equipment'))
    requested_extras = []
    for fe in fe_list:
        qty = int(data.get(f'quantity_{fe.id}', 0) or 0)
        if qty > 0:
            requested_extras.append({'fe': fe, 'quantity': qty, 'unit_price': fe.price_per_unit})

    total = compute_total(field.price_hour, start, end, [
        {'quantity': r['quantity'], 'unit_price': r['unit_price']} for r in requested_extras
    ])

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                booking, payment, _ = confirm_payment_and_create_booking(
                    user=user, field=field, start=start, end=end,
                    extras=requested_extras, form=form
                )
            except ValueError as e:
                messages.error(request, str(e))
                return redirect(reverse('field:list'))
            messages.success(request, "¡Pago realizado y reserva creada!")
            return redirect(reverse('booking:detail', args=[booking.id]))  # crea/asegura esta vista
    else:
        form = PaymentForm()

    return render(request, 'payments/checkout.html', {
        'field': field, 'start': start, 'end': end,
        'extras': requested_extras, 'total': total, 'form': form,
    })
