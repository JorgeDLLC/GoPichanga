from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

class UserRole(models.TextChoices):
    REGULAR = "regular", _("Regular")
    PARTNER = "partner", _("Partner")

class User(models.Model):
    nombre = models.CharField(max_length=150)
    email = models.EmailField(unique=True, db_index=True)
    password = models.CharField(max_length=128) 
    telefono = models.CharField(max_length=15, blank=True, null=True)

    rol = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.REGULAR,
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(default=True)

    class Meta:
        ordering = ["-fecha_registro"]
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["rol"]),
        ]

    def __str__(self):
        return f'User {self.id} - {self.nombre} - {self.get_rol_display()}'

    # Helpers útiles
    @property
    def es_regular(self) -> bool:
        return self.rol == UserRole.REGULAR

    @property
    def es_partner(self) -> bool:
        return self.rol == UserRole.PARTNER


class Regular(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="regular_profile"
    )
    fecha_nacimiento = models.DateField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Perfil Regular"
        verbose_name_plural = "Perfiles Regular"

    def __str__(self):
        return f'Regular {self.id} - {self.user.nombre}'


class Partner(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="partner_profile",
        limit_choices_to={"rol": UserRole.PARTNER},
    )
    cci = models.CharField(
        "Cuenta Interbancaria (CCI)",
        max_length=20,
        unique=True,
        validators=[RegexValidator(r"^\d{20}$", "El CCI debe tener exactamente 20 dígitos.")],
        help_text="Número CCI de 20 dígitos (Perú)."
    )

    dni = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name = "Socio"
        verbose_name_plural = "Socios"

    def __str__(self):
        return f'Partner {self.id} - {self.user.nombre}'

    def clean(self):
        if self.user and self.user.rol != UserRole.PARTNER:
            from django.core.exceptions import ValidationError
            raise ValidationError("El usuario asociado debe tener rol 'partner'.")
