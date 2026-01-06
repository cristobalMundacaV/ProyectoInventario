from django.contrib import admin
from .models import Actividad


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'usuario', 'tipo_accion', 'descripcion')
    list_filter = ('tipo_accion', 'usuario', 'fecha_hora')
    search_fields = ('usuario__username', 'descripcion')
    readonly_fields = ('fecha_hora',)
    ordering = ('-fecha_hora',)


# Auto-register remaining models in this app (preserves custom registrations)
from django.apps import apps
app_models = apps.get_app_config('auditoria').get_models()
for model in app_models:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
