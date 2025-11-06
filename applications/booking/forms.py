from django import forms
from django.utils import timezone
from datetime import datetime, timedelta


class BookingForm(forms.Form):
    date       = forms.DateField(
        label="Fecha",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    start_time = forms.TimeField(
        label="Hora inicio",
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    end_time   = forms.TimeField(
        label="Hora fin",
        widget=forms.TimeInput(attrs={'type': 'time'})
    )

    MIN_SLOT_MINUTES = 60  # variable

    def clean(self):
        cleaned = super().clean()
        d  = cleaned.get('date')
        t1 = cleaned.get('start_time')
        t2 = cleaned.get('end_time')
        if not (d and t1 and t2):
            return cleaned

        # Combina fecha + horas (naive)
        start_naive = datetime.combine(d, t1)
        end_naive   = datetime.combine(d, t2)

        if start_naive >= end_naive:
            self.add_error('end_time', 'La hora fin debe ser posterior a la hora inicio.')
            return cleaned

        # No permitir reservar en pasado
        now_local = timezone.localtime()
        if timezone.is_naive(now_local):
            # normalizar por si acaso (en Django normalmente ahora es aware)
            now_local = timezone.make_aware(now_local, timezone.get_current_timezone())

        # Vuelve aware los datetimes del form en la TZ actual
        tz = timezone.get_current_timezone()
        start = timezone.make_aware(start_naive, tz)
        end   = timezone.make_aware(end_naive, tz)

        if start < now_local:
            self.add_error('date', 'No puedes reservar en el pasado.')

        # Validar múltiplos de MIN_SLOT_MINUTES (opcional)
        delta_start = (start.minute % self.MIN_SLOT_MINUTES)
        delta_end   = (end.minute % self.MIN_SLOT_MINUTES)
        if delta_start != 0 or delta_end != 0:
            msg = f'Las horas deben ser múltiplos de {self.MIN_SLOT_MINUTES} minutos (ej. 10:00, 10:30).'
            if delta_start != 0:
                self.add_error('start_time', msg)
            if delta_end != 0:
                self.add_error('end_time', msg)

        cleaned['start_dt'] = start
        cleaned['end_dt']   = end
        return cleaned


class ExtrasQuantitiesForm(forms.Form):
    """
    Form dinámico: recibe la lista de FieldEquipment (fe_list) y crea
    campos quantity_<fe.id> (IntegerField) para pedir cantidades.
    """
    def __init__(self, *args, fe_list=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fe_list = fe_list or []
        for fe in self.fe_list:
            self.fields[f'quantity_{fe.id}'] = forms.IntegerField(
                label=fe.equipment.get_type_display(),
                min_value=0,
                required=False,
                initial=0,
                widget=forms.NumberInput(attrs={'min': '0'})
            )
