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
        if self.tipo_producto == 'GRANEL':
            return str(self.stock_minimo or 0)
        return str(int(self.stock_minimo or 0))

    @property
    def stock_base_display(self):
        if self.tipo_producto == 'GRANEL':
            return str(self.stock_base or 0)
        return str(int(self.stock_base or 0))
    
    codigo_barra = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50)
    tipo_producto = models.CharField(max_length=10, choices=TipoProducto.choices)
    unidad_base = models.CharField(max_length=10, choices=UnidadBase.choices)

    stock_base = models.DecimalField(max_digits=10, decimal_places=3)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=3)

    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    margen_ganancia = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)

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

    @property
    def margen_display(self):
        if self.tipo_producto == 'PACK' and self.unidades_por_pack:
            try:
                return str(round(float(self.precio_venta) - float(self.precio_unitario_pack), 2))
            except (ZeroDivisionError, TypeError):
                return ""
        elif self.tipo_producto == 'GRANEL' and self.kg_por_caja:
            try:
                # MARGEN POR KG: precio_venta - (precio_compra / kg_por_caja)
                return str(round(float(self.precio_venta) - (float(self.precio_compra) / float(self.kg_por_caja)), 2))
            except (ZeroDivisionError, TypeError):
                return ""
        else:
            return str(round(float(self.precio_venta) - float(self.precio_compra), 2))

    @property
    def precio_unitario_pack(self):
        if self.tipo_producto == 'PACK' and self.unidades_por_pack:
            try:
                return round(float(self.precio_compra) / self.unidades_por_pack, 2)
            except (ZeroDivisionError, TypeError):
                return 0
        return None

    def save(self, *args, **kwargs):
        if self.tipo_producto == 'PACK' and self.unidades_por_pack:
            try:
                self.margen_ganancia = round(float(self.precio_venta) - (float(self.precio_compra) / self.unidades_por_pack), 2)
            except (ZeroDivisionError, TypeError):
                self.margen_ganancia = 0
        elif self.tipo_producto == 'GRANEL' and self.kg_por_caja:
            try:
                # MARGEN POR KG: precio_venta - (precio_compra / kg_por_caja)
                self.margen_ganancia = round(float(self.precio_venta) - (float(self.precio_compra) / float(self.kg_por_caja)), 2)
            except (ZeroDivisionError, TypeError):
                self.margen_ganancia = 0
        else:
            self.margen_ganancia = round(float(self.precio_venta) - float(self.precio_compra), 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
