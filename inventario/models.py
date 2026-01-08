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
        ('PACK', 'Pack'),
        ('KG', 'Kg'),
    ]

    codigo_barra = models.CharField(max_length=50, unique=True, blank=True, null=True)
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

    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    margen_ganancia = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)

    unidades_por_pack = models.IntegerField(blank=True, null=True)
    kg_por_caja = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)

    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def stock_display(self):
        if self.tipo_producto == 'GRANEL':
            return f"{self.stock_actual_base} kg"
        # Si el producto es PACK pero se vende por unidad, mostrar el stock en unidades
        if self.tipo_producto == 'PACK' and self.unidad_base == 'UNIDAD' and self.unidades_por_pack:
            return int(self.stock_actual_base) * int(self.unidades_por_pack)
        return int(self.stock_actual_base)

    @property
    def stock_minimo_display(self):
        if self.tipo_producto == 'GRANEL':
            return f"{self.stock_minimo or 0} kg"
        return str(int(self.stock_minimo or 0))

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

    def registrar_compra(self, cantidad_cajas=None, unidades_por_pack=None, cantidad_unidades=None):
        """
        Actualiza el stock_actual_base según la unidad_base:
        - Si unidad_base es 'UNIDAD', stock en unidades (cajas * unidades_por_pack)
        - Si unidad_base es 'PACK', stock en packs (cajas)
        - Si se agregan unidades sueltas, suma directamente
        """
        if self.unidad_base == 'UNIDAD' and cantidad_cajas and unidades_por_pack:
            # El stock_actual_base es el total de unidades (no suma incremental)
            self.stock_actual_base = int(cantidad_cajas) * int(unidades_por_pack)
        elif self.unidad_base == 'PACK' and cantidad_cajas:
            self.stock_actual_base = int(cantidad_cajas)
        elif cantidad_unidades:
            self.stock_actual_base = float(self.stock_actual_base or 0) + int(cantidad_unidades)
        self.save()

    def save(self, *args, **kwargs):
        # Ajuste y cálculo de margen
        if self.tipo_producto == 'PACK' and self.unidades_por_pack:
            try:
                self.margen_ganancia = round(float(self.precio_venta) - (float(self.precio_compra) / self.unidades_por_pack), 2)
            except (ZeroDivisionError, TypeError):
                self.margen_ganancia = 0
        elif self.tipo_producto == 'GRANEL' and self.kg_por_caja:
            try:
                self.margen_ganancia = round(float(self.precio_venta) - (float(self.precio_compra) / float(self.kg_por_caja)), 2)
            except (ZeroDivisionError, TypeError):
                self.margen_ganancia = 0
        else:
            self.margen_ganancia = round(float(self.precio_venta) - float(self.precio_compra), 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


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
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    cantidad_base = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )

    def __str__(self):
        return f"{self.producto} +{self.cantidad_base}"
