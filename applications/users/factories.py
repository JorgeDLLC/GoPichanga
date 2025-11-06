from dataclasses import dataclass
from typing import Optional
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from .models import User, Regular, UserRole


@dataclass(frozen=True)
class RegularUserInput:
    nombre: str
    email: str
    password: str
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[str] = None  
    direccion: Optional[str] = None

class UserFactory:
    @staticmethod
    @transaction.atomic
    def create_regular(data: RegularUserInput) -> User:
        if not data.nombre or not data.email or not data.password:
            raise ValidationError("nombre, email y password son obligatorios.")
        try:
            user = User.objects.create(
                nombre=data.nombre,
                email=data.email,
                password=data.password,
                telefono=data.telefono,
                rol=UserRole.REGULAR,
                estado=True,
            )
        except IntegrityError:
            raise ValidationError("El email ya está registrado.")

        Regular.objects.create(
            user=user,
            fecha_nacimiento=data.fecha_nacimiento,
            direccion=data.direccion,
        )
        return user
