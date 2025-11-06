from django.urls import path
from . import views

urlpatterns = [
    path('reporting/', views.indexView.as_view())
]