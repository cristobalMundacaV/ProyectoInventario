from django.contrib import admin
from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo_barra', 'nombre', 'categoria', 'tipo_producto', 'stock_display', 'precio_venta', 'activo')
    list_filter = ('categoria', 'tipo_producto', 'activo')
    search_fields = ('codigo_barra', 'nombre', 'categoria')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('codigo_barra', 'nombre', 'categoria', 'tipo_producto', 'unidad_base', 'activo')}),
        ('Stock y precios', {'fields': ('stock_base', 'stock_minimo', 'precio_compra', 'precio_venta', 'margen_ganancia')}),
        ('Opcionales', {'fields': ('unidades_por_pack', 'kg_por_caja')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
