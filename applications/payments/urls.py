# applications/payments/urls.py
from django.urls import path
from .views import checkout_view

app_name = 'payments'
urlpatterns = [
    path('checkout/<int:field_id>/', checkout_view, name='checkout'),
]
