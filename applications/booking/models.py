from django.db import models
from django.core.validators import MinValueValidator
from applications.users.models import User
from applications.field.models import Field, FieldEquipment

class BookingStatus(models.TextChoices):
    PENDING   = 'pending',   'Pendiente'
    CONFIRMED = 'confirmed', 'Confirmada'
    CANCELED  = 'canceled',  'Cancelada'

class Booking(models.Model):
    user   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    field  = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='bookings')
    start  = models.DateTimeField()
    end    = models.DateTimeField()
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    class Meta:
        indexes = [models.Index(fields=['field','start','end','status'])]

    def __str__(self):
        return f'Reserva {self.id} · {self.field.name} · {self.start:%Y-%m-%d %H:%M}'

class BookingExtra(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='extras')
    field_equipment = models.ForeignKey(FieldEquipment, on_delete=models.PROTECT, related_name='booking_extras')
    quantity   = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f'Extra · {self.field_equipment.equipment.get_type_display()} x{self.quantity} (S/ {self.unit_price})'
