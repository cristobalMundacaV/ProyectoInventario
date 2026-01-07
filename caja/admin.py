# caja/admin.py
from django.contrib import admin
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

    def save_model(self, request, obj, form, change):
        if not change:
            obj.hora_apertura = timezone.now()

        if change and not obj.abierta and obj.hora_cierre is None:
            obj.hora_cierre = timezone.now()

        super().save_model(request, obj, form, change)
