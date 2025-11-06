from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import ValidationError
from .forms import RegularCreateForm
from .factories import UserFactory, RegularUserInput

def crear_usuario_regular_view(request):
    if request.method == "POST":
        form = RegularCreateForm(request.POST)
        if form.is_valid():
            try:
                inp = RegularUserInput(
                    nombre=form.cleaned_data["nombre"],
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                    telefono=form.cleaned_data.get("telefono"),
                    fecha_nacimiento=form.cleaned_data.get("fecha_nacimiento"),
                    direccion=form.cleaned_data.get("direccion"),
                )
                user = UserFactory.create_regular(inp)
                messages.success(request, f"Usuario creado: {user.nombre}")
                return redirect(reverse("users:login"))
            except ValidationError as e:
                form.add_error(None, e.message)
            except Exception:
                form.add_error(None, "Ocurrió un error inesperado. Intenta nuevamente.")
    else:
        form = RegularCreateForm()

    return render(request, "users/regular_create.html", {"form": form})

def regular_creado_view(request):
    return render(request, "users/regular_creado.html")

from .models import User, UserRole
from .forms import LoginForm

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            password = form.cleaned_data['password']

            try:
                user = User.objects.get(email=email, password=password)
                request.session['user_id'] = user.id   # guardar sesión
                request.session['user_role'] = user.rol

                messages.success(request, f"Bienvenido {user.nombre}")
                
                # Redirección según rol
                if user.rol == UserRole.PARTNER:
                    return redirect(reverse('partners:day'))  # Página de socio FALTA CREAR
                else:
                    return redirect(reverse('field:list'))  # Página regular
                
            except User.DoesNotExist:
                messages.error(request, "Credenciales inválidas")
    else:
        form = LoginForm()
    
    return render(request, 'users/login.html', {'form': form})

from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache

@require_POST
def logout_view(request):
    # limpia mensajes pendientes
    storage = messages.get_messages(request)
    for _ in storage: 
        pass
    storage.used = True

    request.session.flush()          # borra sesión y cookie
    messages.info(request, "Sesión cerrada correctamente")
    return redirect('users:login')