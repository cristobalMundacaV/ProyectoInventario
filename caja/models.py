from django.db import models
from usuarios.models import Usuario


class Caja(models.Model):
    fecha = models.DateField(unique=True)

    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    total_vendido = models.DecimalField(max_digits=10, decimal_places=2)
    total_efectivo = models.DecimalField(max_digits=10, decimal_places=2)
    total_debito = models.DecimalField(max_digits=10, decimal_places=2)
    total_transferencia = models.DecimalField(max_digits=10, decimal_places=2)
    ganancia_diaria = models.DecimalField(max_digits=10, decimal_places=2)

    abierta = models.BooleanField(default=True)
    hora_apertura = models.DateTimeField()
    hora_cierre = models.DateTimeField(blank=True, null=True)

    abierta_por = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name='cajas_abiertas'
    )
    cerrada_por = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name='cajas_cerradas',
        blank=True, null=True
    )

    def __str__(self):
        return f"Caja {self.fecha}"
