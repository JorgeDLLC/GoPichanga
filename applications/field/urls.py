from django.urls import path
from .views import indexView, fieldCreateCreateView

app_name = 'field'

urlpatterns = [
    path('', indexView.as_view(), name='list'),
    path('create/', fieldCreateCreateView.as_view(), name='create'),         
]