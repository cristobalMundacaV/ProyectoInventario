from django.db import models


class Caja(models.Model):
    fecha = models.DateField(unique=True)
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2)

    total_vendido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_debito = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_transferencia = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    ganancia_diaria = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    abierta = models.BooleanField(default=True)

    def __str__(self):
        return f"Caja {self.fecha}"
