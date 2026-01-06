from django.db import models
from core.enums import TipoProducto, UnidadBase
from usuarios.models import Usuario

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    @property
    def stock_minimo_display(self):
        if self.tipo_producto in ['PACK', 'UNIDAD']:
            return int(self.stock_minimo)
        return self.stock_minimo

    codigo_barra = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50)
    tipo_producto = models.CharField(max_length=10, choices=TipoProducto.choices)
    unidad_base = models.CharField(max_length=10, choices=UnidadBase.choices)

    stock_base = models.DecimalField(max_digits=10, decimal_places=3)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=3)

    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    margen_ganancia = models.DecimalField(max_digits=5, decimal_places=2)

    unidades_por_pack = models.IntegerField(blank=True, null=True)
    kg_por_caja = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)

    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def stock_display(self):
        if self.tipo_producto == 'GRANEL':
            return self.stock_base
        return int(self.stock_base)

    def __str__(self):
        return self.nombre
