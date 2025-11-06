from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions


# ---------- Catálogo de equipamiento ----------
class Equipment(models.Model):
    TYPE_CHOICES = (
        ('balon_futbol', 'Balón de Fútbol'),
        ('balon_basket', 'Balón de Básquet'),
        ('balon_voley',  'Balón de Vóley'),
        ('chalecos',     'Chalecos de Entrenamiento'),
        ('conos',        'Conos de Entrenamiento'),
        ('cronometro',   'Cronómetro'),
        ('raquetas_tenis', 'Raquetas de Tenis'),
        ('pelotas_tenis',  'Pelotas de Tenis'),
        ('cuerda_saltar',  'Cuerdas para Saltar'),
        ('colchonetas',    'Colchonetas'),
        ('pesas_mancuernas', 'Pesas / Mancuernas'),
    )
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='balon_futbol')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.get_type_display()


# ---------- Cancha ----------
class Field(models.Model):
    owner = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=150)

    TYPE_CHOICES = (
        ('futbol',   'Fútbol'),
        ('basket',   'Basketball'),
        ('voley',    'Volleyball'),
        ('tenis',    'Tenis'),
        ('multiuso', 'Multiuso'),
    )
    type = models.CharField(max_length=100, choices=TYPE_CHOICES, default='multiuso')
    address = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price_hour = models.DecimalField(max_digits=10, decimal_places=2)
    has_lights = models.BooleanField(default=False)

    # relación M2M con tabla intermedia para manejar stock y precio de alquiler
    extra_equipment = models.ManyToManyField(
        Equipment,
        through='FieldEquipment',
        related_name='fields',
        blank=True,
    )

    def __str__(self):
        return f'Field {self.id} - {self.name} - Owner {self.owner.nombre}'

    @property
    def primary_image(self):
        primary = self.albums.filter(is_primary=True).first()
        return primary or self.albums.order_by('sort_order', 'id').first()


# ---------- Equipamiento por cancha (stock + precio alquiler) ----------
class FieldEquipment(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='field_equipments')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='equipment_fields')

    # stock disponible en esta cancha
    stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])

    # precio de alquiler por unidad (p.ej. S/ por chaleco)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    class Meta:
        # evita duplicados field+equipment
        constraints = [
            models.UniqueConstraint(fields=['field', 'equipment'], name='uniq_field_equipment'),
        ]

    def __str__(self):
        return (
            f'{self.field.name} · {self.equipment.get_type_display()} · '
            f'stock {self.stock} · S/ {self.price_per_unit}/u'
        )


# ---------- Álbum de imágenes ----------
class Album(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='albums')
    image = models.ImageField(upload_to='field_albums/')  # se servirá en /media/field_albums/
    is_primary = models.BooleanField(default=False, help_text="Marca esta imagen como la principal del campo.")
    sort_order = models.PositiveIntegerField(default=0, help_text="Orden de la imagen en el álbum.")

    class Meta:
        ordering = ['sort_order']
        constraints = [
            # asegura que haya a lo sumo 1 imagen principal por cancha
            models.UniqueConstraint(
                fields=['field'],
                condition=models.Q(is_primary=True),
                name='unique_primary_image_per_field',
            )
        ]

    def __str__(self):
        return f'Album {self.id} - Field {self.field.name} - Primary {self.is_primary}'

    def clean(self):
        super().clean()
        if not self.image:
            return

        # Validaciones de imagen (dimensiones/peso)
        min_w, min_h = 1024, 768
        max_w, max_h = 4096, 4096
        max_size_mb = 4

        size_mb = (self.image.size or 0) / (1024 * 1024)
        if size_mb > max_size_mb:
            raise ValidationError({'image': f'La imagen pesa {size_mb:.2f}MB; máximo {max_size_mb}MB.'})

        w, h = get_image_dimensions(self.image)
        if w is None or h is None:
            raise ValidationError({'image': 'No se pudieron obtener las dimensiones.'})
        if w < min_w or h < min_h:
            raise ValidationError({'image': f'Mínimo {min_w}×{min_h}px. Subiste {w}×{h}px.'})
        if w > max_w or h > max_h:
            raise ValidationError({'image': f'Máximo {max_w}×{max_h}px. Subiste {w}×{h}px.'})
