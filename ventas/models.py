from django.db import models
from core.enums import MetodoPago, UnidadVenta
from usuarios.models import Usuario
from caja.models import Caja
from inventario.models import Producto

class Venta(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=15, choices=MetodoPago.choices)
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT)

class VentaDetalle(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)

    cantidad_ingresada = models.DecimalField(max_digits=10, decimal_places=3)
    unidad_venta = models.CharField(max_length=10, choices=UnidadVenta.choices)
    cantidad_base = models.DecimalField(max_digits=10, decimal_places=3)

    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
