from django.db import models
from django.core.validators import MinValueValidator

class PaymentMethod(models.TextChoices):
    CARD = 'card', 'Tarjeta'

class PaymentStatus(models.TextChoices):
    PENDING   = 'pending',   'Pendiente'
    APPROVED  = 'approved',  'Aprobado'
    DECLINED  = 'declined',  'Rechazado'

class Payment(models.Model):
    booking = models.ForeignKey('booking.Booking', on_delete=models.CASCADE, related_name='payments')
    method  = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CARD)
    status  = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    amount  = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    holder_name = models.CharField(max_length=120, blank=True, null=True)
    card_brand  = models.CharField(max_length=20, blank=True, null=True)
    last4       = models.CharField(max_length=4,  blank=True, null=True)
    auth_code   = models.CharField(max_length=16, blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Payment {self.id} · {self.status} · S/ {self.amount}'
