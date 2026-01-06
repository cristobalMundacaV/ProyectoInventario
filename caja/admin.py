from django.contrib import admin
from django.utils import timezone
from .models import Caja


@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'monto_inicial', 'total_vendido', 'abierta')
    list_filter = ('abierta',)
    search_fields = ('fecha',)
    readonly_fields = ('hora_apertura', 'hora_cierre')
    date_hierarchy = 'fecha'

    def save_model(self, request, obj, form, change):
        # If creating a new Caja and hora_apertura not provided, set it to now
        if not change and not obj.hora_apertura:
            obj.hora_apertura = timezone.now()
        super().save_model(request, obj, form, change)
