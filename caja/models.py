
from django.db import models
from django.contrib.auth.models import User


class Caja(models.Model):
    fecha = models.DateField()

    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2)

    total_vendido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_debito = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_transferencia = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    ganancia_diaria = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    abierta = models.BooleanField(default=True)

    abierta_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cajas_abiertas')
    cerrada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cajas_cerradas')

    hora_apertura = models.DateTimeField()
    hora_cierre = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Caja {self.fecha} - {self.hora_apertura.strftime('%H:%M')}"
