from django.contrib import admin
from .models import Actividad


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'usuario', 'tipo_accion', 'descripcion')
    list_filter = ('tipo_accion', 'usuario')
    search_fields = ('descripcion', 'usuario__username')
    ordering = ('-fecha_hora',)

    # Auditoría: solo lectura / no editable / no eliminable
    actions = None  # elimina acciones masivas (incluye delete_selected)

    def get_readonly_fields(self, request, obj=None):
        # Todos los campos quedan de solo lectura (inclusive en la vista de detalle)
        try:
            model_fields = [f.name for f in self.model._meta.fields]
        except Exception:
            model_fields = ['fecha_hora', 'usuario', 'tipo_accion', 'descripcion', 'caja']
        return tuple(model_fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        # Permitir ver (GET) pero bloquear cualquier intento de modificación (POST)
        if request.method and request.method.upper() == 'POST':
            return False
        return True
