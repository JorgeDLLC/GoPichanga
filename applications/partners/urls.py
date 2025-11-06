from django.urls import path
from . import views

app_name = 'partners'
urlpatterns = [
    path('', views.day_calendar_view, name='day'),             # default
    path('day/', views.day_calendar_view, name='day'),
    path('week/', views.week_calendar_view, name='week'),
    path('month/', views.month_summary_view, name='month'),
]
