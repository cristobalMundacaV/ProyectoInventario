from django.contrib import admin
from .models import (
    Categoria,
    Producto,
    Presentacion,
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
        'nombre',
        'categoria',
        'tipo_producto',
        'unidad_base',
        'stock_actual_base',
        'stock_minimo',
    )
    list_filter = ('categoria', 'tipo_producto', 'unidad_base')
    search_fields = ('nombre', 'categoria__nombre')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Información del Producto', {
            'fields': (
                'nombre',
                'categoria',
                'tipo_producto',
                'unidad_base',
                'stock_actual_base',
                'stock_minimo',
            )
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


# =========================
# PRESENTACION
# =========================
@admin.register(Presentacion)
class PresentacionAdmin(admin.ModelAdmin):
    list_display = (
        'producto',
        'nombre',
        'codigo_barra',
        'unidad_venta',
        'precio_venta',
        'margen_ganancia',
        'activo',
    )
    def activo(self, obj):
        return obj.producto.stock_actual_base > 0
    activo.boolean = True
    list_filter = ('unidad_venta', 'producto__categoria')
    search_fields = (
        'nombre',
        'codigo_barra',
        'producto__nombre',
    )
    readonly_fields = ('created_at', 'updated_at', 'activo')

    fieldsets = (
        ('Producto', {
            'fields': ('producto', 'nombre', 'codigo_barra')
        }),
        ('Configuración de Venta', {
            'fields': ('unidad_venta',)
        }),
        ('Precios', {
            'fields': (
                'precio_compra',
                'precio_venta',
                'margen_ganancia',
            )
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'activo'),
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
    list_display = ('ingreso', 'presentacion', 'cantidad_base')
    search_fields = ('presentacion__nombre', 'presentacion__codigo_barra')
