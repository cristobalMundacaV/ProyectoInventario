from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nombre


class Producto(models.Model):

    TIPO_PRODUCTO_CHOICES = [
        ('UNITARIO', 'Unitario'),
        ('PACK', 'Pack'),
        ('GRANEL', 'Granel'),
    ]

    UNIDAD_BASE_CHOICES = [
        ('UNIDAD', 'Unidad'),
        ('KG', 'Kilogramo'),
    ]

    nombre = models.CharField(max_length=100)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos'
    )
    tipo_producto = models.CharField(
        max_length=10,
        choices=TIPO_PRODUCTO_CHOICES
    )
    unidad_base = models.CharField(
        max_length=10,
        choices=UNIDAD_BASE_CHOICES
    )

    stock_actual_base = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0
    )

    stock_minimo = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre


class Presentacion(models.Model):

    UNIDAD_VENTA_CHOICES = [
        ('UNIDAD', 'Unidad'),
        ('KG', 'Kilogramo'),
        ('PACK', 'Pack'),
        ('CAJA', 'Caja'),
    ]

    producto = models.ForeignKey(
        Producto,
        related_name='presentaciones',
        on_delete=models.PROTECT
    )

    nombre = models.CharField(max_length=50)
    codigo_barra = models.CharField(max_length=50, unique=True)

    unidad_venta = models.CharField(
        max_length=10,
        choices=UNIDAD_VENTA_CHOICES
    )

    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    margen_ganancia = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        default=0
    )

    unidades_por_pack = models.IntegerField(blank=True, null=True)
    kg_por_caja = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def activo(self):
        return self.producto.stock_actual_base > 0

    @property
    def stock_minimo_display(self):
        if self.producto.tipo_producto == 'GRANEL':
            return str(self.producto.stock_minimo or 0)
        return str(int(self.producto.stock_minimo or 0))

    @property
    def stock_base_display(self):
        if self.producto.tipo_producto == 'GRANEL':
            return str(self.producto.stock_actual_base or 0)
        return str(int(self.producto.stock_actual_base or 0))

    @property
    def stock_display(self):
        if self.producto.tipo_producto == 'GRANEL':
            return self.producto.stock_actual_base
        return int(self.producto.stock_actual_base)

    @property
    def margen_display(self):
        if self.unidad_venta == 'PACK' and self.unidades_por_pack:
            try:
                return str(round(float(self.precio_venta) - float(self.precio_unitario_pack), 2))
            except (ZeroDivisionError, TypeError):
                return ""
        elif self.unidad_venta == 'CAJA' and self.kg_por_caja:
            try:
                # MARGEN POR KG: precio_venta - (precio_compra / kg_por_caja)
                return str(round(float(self.precio_venta) - (float(self.precio_compra) / float(self.kg_por_caja)), 2))
            except (ZeroDivisionError, TypeError):
                return ""
        else:
            return str(round(float(self.precio_venta) - float(self.precio_compra), 2))

    @property
    def precio_unitario_pack(self):
        if self.unidad_venta == 'PACK' and self.unidades_por_pack:
            try:
                return round(float(self.precio_compra) / self.unidades_por_pack, 2)
            except (ZeroDivisionError, TypeError):
                return 0
        return None

    def save(self, *args, **kwargs):
        if self.unidad_venta == 'PACK' and self.unidades_por_pack:
            try:
                self.margen_ganancia = round(float(self.precio_venta) - (float(self.precio_compra) / self.unidades_por_pack), 2)
            except (ZeroDivisionError, TypeError):
                self.margen_ganancia = 0
        elif self.unidad_venta == 'CAJA' and self.kg_por_caja:
            try:
                # MARGEN POR KG: precio_venta - (precio_compra / kg_por_caja)
                self.margen_ganancia = round(float(self.precio_venta) - (float(self.precio_compra) / float(self.kg_por_caja)), 2)
            except (ZeroDivisionError, TypeError):
                self.margen_ganancia = 0
        else:
            self.margen_ganancia = round(float(self.precio_venta) - float(self.precio_compra), 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} - {self.nombre}"

class IngresoStock(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT
    )
    observacion = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"Ingreso {self.id} - {self.fecha.date()}"

class IngresoStockDetalle(models.Model):
    ingreso = models.ForeignKey(
        IngresoStock,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    presentacion = models.ForeignKey(
        Presentacion,
        on_delete=models.PROTECT
    )
    cantidad_base = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )

    def __str__(self):
        return f"{self.presentacion} +{self.cantidad_base}"
