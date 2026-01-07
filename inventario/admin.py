from django.contrib import admin
from .models import (
    Categoria,
    Producto,
    IngresoStock,
    IngresoStockDetalle
)


# =========================
# CATEGORIA
# =========================
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)
    ordering = ('nombre',)


# =========================
# PRODUCTO
# =========================
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_barra',
        'nombre',
        'categoria',
        'tipo_producto',
        'unidad_base',
        'stock_actual_base',
        'stock_minimo',
        'precio_compra',
        'precio_venta',
        'margen_ganancia',
        'activo',
    )
    list_filter = ('categoria', 'tipo_producto', 'unidad_base')
    search_fields = ('nombre', 'categoria__nombre', 'codigo_barra')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Información del Producto', {
            'fields': (
                'codigo_barra',
                'nombre',
                'categoria',
                'tipo_producto',
                'unidad_base',
                'stock_actual_base',
                'stock_minimo',
                'precio_compra',
                'precio_venta',
                'unidades_por_pack',
                'kg_por_caja',
                'activo',
            )
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


# =========================
# INGRESO DE STOCK
# =========================
class IngresoStockDetalleInline(admin.TabularInline):
    model = IngresoStockDetalle
    extra = 1


@admin.register(IngresoStock)
class IngresoStockAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'usuario', 'observacion')
    search_fields = ('usuario__username',)
    readonly_fields = ('fecha',)
    inlines = (IngresoStockDetalleInline,)


# =========================
# INGRESO STOCK DETALLE
# =========================
@admin.register(IngresoStockDetalle)
class IngresoStockDetalleAdmin(admin.ModelAdmin):
    list_display = ('ingreso', 'producto', 'cantidad_base')
    search_fields = ('producto__nombre', 'producto__codigo_barra')
