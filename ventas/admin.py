from django.contrib import admin
from .models import Venta, VentaDetalle

class VentaDetalleInline(admin.TabularInline):
    model = VentaDetalle
    extra = 0

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'total', 'metodo_pago', 'usuario', 'caja')
    inlines = [VentaDetalleInline]

@admin.register(VentaDetalle)
class VentaDetalleAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto', 'cantidad_ingresada', 'unidad_venta', 'precio_unitario', 'subtotal')
