from django.db import models
from inventario.models import Producto
from caja.models import Caja
from core.enums import MetodoPago


class Venta(models.Model):

    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(
        max_length=15,
        choices=MetodoPago.choices
    )
    usuario = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT
    )
    caja = models.ForeignKey(
        Caja,
        on_delete=models.PROTECT,
        related_name='ventas'
    )

    def __str__(self):
        return f"Venta {self.id}"


class VentaDetalle(models.Model):
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    cantidad_ingresada = models.DecimalField(max_digits=10, decimal_places=3)
    unidad_venta = models.CharField(max_length=10)
    cantidad_base = models.DecimalField(max_digits=10, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.producto} x {self.cantidad_ingresada}"


class Fiado(models.Model):
    ESTADO_CHOICES = [
        ('ABIERTO', 'Abierto'),
        ('PAGADO', 'Pagado'),
        ('ANULADO', 'Anulado'),
    ]

    fecha = models.DateTimeField(auto_now_add=True)
    cliente_nombre = models.CharField(max_length=120)
    cliente_telefono = models.CharField(max_length=30, blank=True)
    cliente_rut = models.CharField(max_length=20, blank=True)

    total = models.DecimalField(max_digits=10, decimal_places=2)
    saldo = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='ABIERTO')
    observacion = models.CharField(max_length=255, blank=True)

    usuario = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='fiados')

    def __str__(self):
        return f"Fiado {self.id} - {self.cliente_nombre}"


class FiadoDetalle(models.Model):
    fiado = models.ForeignKey(Fiado, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad_ingresada = models.DecimalField(max_digits=10, decimal_places=3)
    unidad_venta = models.CharField(max_length=10)
    cantidad_base = models.DecimalField(max_digits=10, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.producto} x {self.cantidad_ingresada} ({self.fiado_id})"


class FiadoAbono(models.Model):
    fiado = models.ForeignKey(Fiado, on_delete=models.CASCADE, related_name='abonos')
    fecha = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=15, choices=MetodoPago.choices)
    referencia = models.CharField(max_length=60, blank=True)

    usuario = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='abonos_fiado')

    def __str__(self):
        return f"Abono fiado {self.fiado_id} - {self.monto}"
