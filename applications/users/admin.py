from django.contrib import admin
from .models import User, Regular, Partner

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("nombre", "email", "rol", "estado", "fecha_registro")
    list_filter = ("rol", "estado")
    search_fields = ("nombre", "email", "telefono")

admin.site.register(Regular)
@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("user", "dni", "cci")
    search_fields = ("user__nombre", "user__email", "dni", "cci")
