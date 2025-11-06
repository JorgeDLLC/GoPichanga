from django.db import models

# Create your models here.
class Schedule(models.Model):
    field = models.ForeignKey('field.Field', on_delete=models.CASCADE, related_name='schedules')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='schedules')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=50, default='true')  # true= disponible, false= no ocupado

    def __str__(self):
        return f'Schedule {self.id} - {self.field.nombre} - {self.user.nombre}'