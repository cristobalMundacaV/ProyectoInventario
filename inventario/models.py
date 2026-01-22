from django.db import models
from django.db.models import Case, DecimalField, ExpressionWrapper, F, When
from django.utils import timezone


_STOCK_DECIMAL_FIELD = DecimalField(max_digits=10, decimal_places=3)


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
            try:
                return f"{float(self.stock_actual_base):.2f} kg"
            except Exception:
                return f"{self.stock_actual_base} kg"
        # Si el producto es PACK pero se vende por unidad, mostrar el stock en unidades
        if self.tipo_producto == 'PACK' and self.unidad_base == 'UNIDAD' and self.unidades_por_pack:
            return int(self.stock_actual_base) * int(self.unidades_por_pack)
        return int(self.stock_actual_base)

    def stock_actual_para_alerta(self):
        """Stock actual en la misma unidad que se compara con el mínimo.

        Para PACK vendidos por UNIDAD, el stock se muestra en unidades (packs * unidades_por_pack),
        y el mínimo se interpreta en unidades; por lo tanto la comparación debe hacerse en unidades.
        """
        try:
            if self.tipo_producto == 'PACK' and self.unidad_base == 'UNIDAD' and self.unidades_por_pack:
                return (self.stock_actual_base or 0) * int(self.unidades_por_pack)
            return self.stock_actual_base or 0
        except Exception:
            return self.stock_actual_base or 0

    def stock_minimo_para_alerta(self):
        """Stock mínimo en la unidad de comparación.

        En la UI, para PACK con unidad_base=UNIDAD el mínimo se ingresa/visualiza en unidades,
        por lo que no se convierte.
        """
        return self.stock_minimo or 0

    def is_stock_bajo(self):
        try:
            if (self.stock_minimo or 0) <= 0:
                return False
            return (self.stock_actual_para_alerta() or 0) <= (self.stock_minimo_para_alerta() or 0)
        except Exception:
            return False

    @property
    def stock_minimo_display(self):
        if self.tipo_producto == 'GRANEL':
            try:
                return f"{float(self.stock_minimo or 0):.2f} kg"
            except Exception:
                return f"{self.stock_minimo or 0} kg"
        try:
            return str(int(self.stock_minimo or 0))
        except Exception:
            return str(self.stock_minimo or 0)

    @property
    def margen_display(self):
        if self.tipo_producto == 'PACK' and self.unidades_por_pack:
            try:
                # Si el pack se vende por UNIDAD, el margen es por unidad.
                # Si el pack se vende por PACK, el margen es por pack.
                if self.unidad_base == 'PACK':
                    return str(round(float(self.precio_venta) - float(self.precio_compra), 2))
                # Nota: para PACK vendido por UNIDAD, precio_compra se guarda como costo por unidad.
                return str(round(float(self.precio_venta) - float(self.precio_compra), 2))
            except (ZeroDivisionError, TypeError):
                return ""
        elif self.tipo_producto == 'GRANEL' and self.kg_por_caja:
            try:
                # Nota: para GRANEL, precio_compra se guarda como costo por KG.
                return str(round(float(self.precio_venta) - float(self.precio_compra), 2))
            except (ZeroDivisionError, TypeError):
                return ""
        else:
            return str(round(float(self.precio_venta) - float(self.precio_compra), 2))

    @property
    def precio_unitario_pack(self):
        if self.tipo_producto == 'PACK' and self.unidades_por_pack:
            try:
                # Si unidad_base=UNIDAD, ya guardamos el costo unitario en precio_compra.
                if self.unidad_base == 'UNIDAD':
                    return round(float(self.precio_compra), 2)
                # Si unidad_base=PACK, devolvemos un costo unitario de referencia.
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
                if self.unidad_base == 'PACK':
                    # Margen por pack (precio_venta por pack - costo del pack)
                    self.margen_ganancia = round(float(self.precio_venta) - float(self.precio_compra), 2)
                else:
                    # Para venta por UNIDAD, guardamos precio_compra como costo por unidad.
                    self.margen_ganancia = round(float(self.precio_venta) - float(self.precio_compra), 2)
            except (ZeroDivisionError, TypeError):
                self.margen_ganancia = 0
        elif self.tipo_producto == 'GRANEL' and self.kg_por_caja:
            try:
                # Para GRANEL, guardamos precio_compra como costo por KG.
                self.margen_ganancia = round(float(self.precio_venta) - float(self.precio_compra), 2)
            except (ZeroDivisionError, TypeError):
                self.margen_ganancia = 0
        else:
            self.margen_ganancia = round(float(self.precio_venta) - float(self.precio_compra), 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class IngresoStock(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('FACTURA', 'Factura'),
        ('REMITO', 'Remito'),
        ('RECEPCION', 'Recepción'),
        ('OTRO', 'Otro'),
    ]

    fecha = models.DateTimeField(default=timezone.now)
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOCUMENTO_CHOICES, default='OTRO')
    numero_documento = models.CharField(max_length=50, blank=True, null=True)
    proveedor = models.CharField(max_length=100, blank=True, null=True)
    usuario = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT
    )
    observacion = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        doc = self.tipo_documento
        if self.numero_documento:
            doc = f"{doc} {self.numero_documento}"
        return f"Ingreso {self.id} - {self.fecha.date()} - {doc}"


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


def annotate_stock_actual_alerta(qs):
    """Anota `stock_actual_alerta` para filtrar bajo-stock en DB.

    Regla especial: PACK con unidad_base=UNIDAD compara en unidades (packs * unidades_por_pack).
    """
    if qs is None:
        qs = Producto.objects.all()

    stock_actual_alerta = Case(
        When(
            tipo_producto='PACK',
            unidad_base='UNIDAD',
            unidades_por_pack__gt=0,
            then=ExpressionWrapper(
                F('stock_actual_base') * F('unidades_por_pack'),
                output_field=_STOCK_DECIMAL_FIELD,
            ),
        ),
        default=F('stock_actual_base'),
        output_field=_STOCK_DECIMAL_FIELD,
    )

    return qs.annotate(stock_actual_alerta=stock_actual_alerta)


def bajo_stock_queryset(qs=None):
    """Devuelve un queryset con productos en bajo stock con reglas consistentes."""
    qs = annotate_stock_actual_alerta(qs)
    return qs.filter(stock_minimo__gt=0).filter(stock_actual_alerta__lte=F('stock_minimo'))
