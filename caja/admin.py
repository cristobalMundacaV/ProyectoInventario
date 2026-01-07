from django.contrib import admin
from django.utils import timezone
from .models import Caja


@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'abierta')
    list_filter = ('abierta', 'fecha')
    search_fields = ('fecha',)
