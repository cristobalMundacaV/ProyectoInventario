from django.contrib import admin
from .models import Actividad


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'usuario', 'tipo_accion', 'descripcion')
    list_filter = ('tipo_accion', 'usuario')
    search_fields = ('descripcion', 'usuario__username')
    readonly_fields = ('fecha_hora',)
    ordering = ('-fecha_hora',)
