from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html   # FIX: importar para usar en previews

from .models import Field, Album, Equipment, FieldEquipment

# ---------- Paso 1: Asegurar 1 sola imagen principal en el inline del álbum ----------
class SinglePrimaryImageInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        primaries = 0
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            if form.cleaned_data.get('DELETE'):
                continue
            if form.cleaned_data.get('is_primary'):
                primaries += 1
        if primaries > 1:
            raise ValidationError("Solo puede haber UNA imagen principal por cancha.")

class AlbumInline(admin.TabularInline):
    model = Album
    formset = SinglePrimaryImageInlineFormSet
    extra = 1
    fields = ('thumb', 'image', 'is_primary', 'sort_order')
    readonly_fields = ('thumb',)
    ordering = ('sort_order',)

    def thumb(self, obj):
        if obj.id and obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:6px;" />', obj.image.url)
        return "—"
    thumb.short_description = "Vista previa"


# ---------- Paso 2: Inline para manejar el M2M con through ----------
class FieldEquipmentInline(admin.TabularInline):
    model = FieldEquipment
    extra = 1
    autocomplete_fields = ('equipment',)  # opcional si activas autocomplete
    # FIX: así editas el stock por cancha/equipo directamente desde Field
    fields = ('equipment', 'stock')


# ---------- Paso 3: Admin de Field (sin extra_equipment en fieldsets) ----------
@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'owner', 'price_hour', 'primary_image_preview')
    list_filter = ('type',)
    search_fields = ('name', 'address', 'owner__nombre')
    inlines = [AlbumInline, FieldEquipmentInline]  # FIX: añadimos FieldEquipmentInline

    fieldsets = (
        ('Información general', {
            'fields': ('owner', 'name', 'type', 'address', 'description')
        }),
        ('Tarifas', {
            'fields': ('price_hour',),
        }),
        # FIX: NO incluir 'extra_equipment' aquí porque es M2M con through => no editable en el form
    )

    def primary_image_preview(self, obj):
        # FIX: asegúrate de tener la property obj.primary_image en tu modelo Field
        album = obj.primary_image
        if album and album.image:
            return format_html('<img src="{}" style="height:60px;border-radius:6px;" />', album.image.url)
        return "—"
    primary_image_preview.short_description = "Imagen principal"


# ---------- Paso 4: Admin de Equipment ----------
@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'description')
    list_filter = ('type',)
    search_fields = ('description',)


# ---------- Paso 5: Admin de FieldEquipment ----------
@admin.register(FieldEquipment)
class FieldEquipmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'field', 'equipment', 'stock')
    list_filter = ('equipment__type',)
    search_fields = ('field__name', 'equipment__description')


# ---------- (Opcional) Admin de Album con acción para marcar principal ----------
@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('id', 'field', 'is_primary', 'sort_order', 'mini')
    list_filter = ('is_primary', 'field__type')
    search_fields = ('field__name',)
    actions = ['marcar_como_principal']

    def mini(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:50px;border-radius:6px;" />', obj.image.url)
        return "—"
    mini.short_description = "Miniatura"

    def marcar_como_principal(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Selecciona exactamente UNA imagen.", level='error')
            return
        album = queryset.first()
        Album.objects.filter(field=album.field, is_primary=True).exclude(id=album.id).update(is_primary=False)
        album.is_primary = True
        album.save(update_fields=['is_primary'])
        self.message_user(request, f"Imagen {album.id} marcada como principal para '{album.field.name}'.")
    marcar_como_principal.short_description = "Marcar como principal (y desmarcar otras)"
