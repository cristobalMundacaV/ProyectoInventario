from django.contrib import admin, messages
from django.utils import timezone

from .models import Caja


@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = (
        'fecha',
        'abierta',
        'hora_apertura',
        'hora_cierre',
        'total_vendido',
    )

    list_filter = ('abierta', 'fecha')
    search_fields = ('fecha',)

    readonly_fields = (
        'hora_apertura',
        'hora_cierre',
        'total_vendido',
        'total_efectivo',
        'total_debito',
        'total_transferencia',
        'ganancia_diaria',
    )

    def get_readonly_fields(self, request, obj=None):
        """Si la caja ya está cerrada, no se permite editar ningún campo desde el Admin."""
        base_readonly = list(super().get_readonly_fields(request, obj))
        if obj is not None:
            try:
                # Usar el estado persistido (DB) para evitar bypass cambiando el checkbox 'abierta'
                persisted_abierta = Caja.objects.filter(pk=obj.pk).values_list('abierta', flat=True).first()
            except Exception:
                persisted_abierta = getattr(obj, 'abierta', None)

            if persisted_abierta is False:
                # Todos los campos del modelo quedan como solo lectura
                model_fields = [f.name for f in obj._meta.fields]
                return tuple(sorted(set(model_fields + base_readonly)))

        return tuple(base_readonly)

    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar cajas cerradas
        if obj is not None:
            try:
                persisted_abierta = Caja.objects.filter(pk=obj.pk).values_list('abierta', flat=True).first()
            except Exception:
                persisted_abierta = getattr(obj, 'abierta', None)
            if persisted_abierta is False:
                return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        # Regla de negocio: una caja cerrada no se puede modificar.
        if change:
            try:
                persisted_abierta = Caja.objects.filter(pk=obj.pk).values_list('abierta', flat=True).first()
            except Exception:
                persisted_abierta = None
            if persisted_abierta is False:
                self.message_user(
                    request,
                    'No se puede modificar una caja que ya está cerrada.',
                    level=messages.ERROR,
                )
                return

        if not change:
            obj.hora_apertura = timezone.now()

        if change and not obj.abierta and obj.hora_cierre is None:
            obj.hora_cierre = timezone.now()

        super().save_model(request, obj, form, change)
