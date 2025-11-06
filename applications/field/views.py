from django.views.generic import ListView, CreateView
from applications.field.models import Field

class indexView(ListView):
    template_name = 'field/field.html'
    model = Field
    paginate_by = 10
    ordering = 'id'                     # <- correcto
    context_object_name = 'listado_fields'

    def get_queryset(self):
        kword = self.request.GET.get('kword', '')
        qs = super().get_queryset()
        if kword:
            qs = qs.filter(type=kword)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['selected_type'] = self.request.GET.get('kword', '')
        ctx['type_choices'] = Field._meta.get_field('type').choices
        return ctx

class fieldCreateCreateView(CreateView):
    model = Field
    template_name = "field_create.html"
    fields = ['name', 'type', 'address', 'description', 'price_hour', 'has_lights', 'extra_equipment']
    success_url = '/scheduling/'