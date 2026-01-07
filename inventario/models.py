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
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=3)

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

    cantidad_base = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )

    stock_base = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0
    )

    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    margen_ganancia = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    @property
    def activo_property(self):
        return self.stock_base > 0

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
    cantidad_base = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return f"{self.presentacion} +{self.cantidad_base}"
