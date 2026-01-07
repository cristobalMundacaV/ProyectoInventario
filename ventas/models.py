from django.db import models
from inventario.models import Presentacion
from caja.models import Caja


class Venta(models.Model):

    METODO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('DEBITO', 'Débito'),
        ('TRANSFERENCIA', 'Transferencia'),
    ]

    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(
        max_length=15,
        choices=METODO_PAGO_CHOICES
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
    presentacion = models.ForeignKey(
        Presentacion,
        on_delete=models.PROTECT
    )
    cantidad_ingresada = models.DecimalField(max_digits=10, decimal_places=3)
    unidad_venta = models.CharField(max_length=10)
    cantidad_base = models.DecimalField(max_digits=10, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.presentacion} x {self.cantidad_ingresada}"
