from django.urls import path
from applications.booking.views import FieldDetailBookingView  # ← importamos la vista integrada
from . import views

app_name = "field"
urlpatterns = [
    path("detalle-cancha/<int:pk>/", FieldDetailBookingView.as_view(), name="detail"),
    path('<int:pk>/editar/',  views.booking_edit_view,   name='edit'),
    path('<int:pk>/eliminar/', views.booking_delete_view, name='delete'),
]