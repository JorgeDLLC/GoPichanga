from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path('regular_create/', views.crear_usuario_regular_view, name='regular_create'),
    path('creado/',         views.regular_creado_view,      name='regular_creado'),
]
