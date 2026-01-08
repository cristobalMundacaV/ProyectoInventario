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
