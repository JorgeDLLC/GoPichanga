# applications/booking/views.py
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from applications.users.models import User
from applications.field.models import Field, FieldEquipment
from .forms import BookingForm, ExtrasQuantitiesForm
from .factories import BookingFactory, ExtraRequest
from .exceptions import BookingError

@method_decorator(never_cache, name="dispatch")
class FieldDetailBookingView(DetailView):
    """
    Detalle público de una cancha (+ formulario de reserva en la misma URL).
    GET  -> muestra detalle + forms
    POST -> valida y crea la reserva; si no hay login, redirige a /users/login?next=...
    """
    model = Field
    template_name = "booking/booking.html"
    context_object_name = "field"

    # ---- GET ----
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        fe_list = FieldEquipment.objects.filter(field=self.object).select_related("equipment")
        ctx["fe_list"] = fe_list
        ctx["form"] = BookingForm()  # fecha/hora
        ctx["extras_form"] = ExtrasQuantitiesForm(fe_list=fe_list)  # cantidades por extra
        return ctx

    # ---- POST (crear reserva) ----
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()  # Field
        fe_list = FieldEquipment.objects.filter(field=self.object).select_related("equipment")

        # Si no hay sesión, manda al login preservando el next
        if not getattr(request, "gp_is_auth", False) and not request.session.get("user_id"):
            login_url = reverse("users:login")
            return redirect(f"{login_url}?next={request.get_full_path()}")

        user = User.objects.get(pk=request.session.get("user_id"))

        form = BookingForm(request.POST)
        extras_form = ExtrasQuantitiesForm(request.POST, fe_list=fe_list)

        if form.is_valid() and extras_form.is_valid():
            start = form.cleaned_data["start_dt"]
            end   = form.cleaned_data["end_dt"]

            # Construye la lista de extras solicitados
            extras_req = []
            for fe in fe_list:
                qty = extras_form.cleaned_data.get(f"quantity_{fe.id}") or 0
                if qty > 0:
                    extras_req.append(ExtraRequest(fe_id=fe.id, quantity=qty))

            try:
                booking = BookingFactory.create(
                    user=user,
                    field=self.object,
                    start=start,
                    end=end,
                    extras=extras_req,
                )
                messages.success(request, "¡Reserva creada!")
                # Redirige a un detalle de la reserva si lo tienes, o vuelve al mismo detalle
                return redirect(reverse("booking:detail", args=[booking.id]))  # ajusta si aún no existe
            except BookingError as e:
                messages.error(request, str(e))

        # Volver a renderizar con errores
        ctx = self.get_context_data()
        ctx["form"] = form
        ctx["extras_form"] = extras_form
        return self.render_to_response(ctx)
