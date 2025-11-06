from django.urls import path
from applications.booking.views import FieldDetailBookingView  # ← importamos la vista integrada

app_name = "field"
urlpatterns = [
    path("detalle-cancha/<int:pk>/", FieldDetailBookingView.as_view(), name="detail"),
]