from django.db import models


class Actividad(models.Model):

    TIPO_ACCION_CHOICES = [
        ('APERTURA_CAJA', 'Apertura de Caja'),
        ('CIERRE_CAJA', 'Cierre de Caja'),
        ('VENTA', 'Venta'),
        ('INGRESO_STOCK', 'Ingreso de Stock'),
        ('CREACION_PRODUCTO', 'Creación de Producto'),
        ('EDICION_PRODUCTO', 'Edición de Producto'),
    ]

    fecha_hora = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT
    )
    tipo_accion = models.CharField(
        max_length=30,
        choices=TIPO_ACCION_CHOICES
    )
    descripcion = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.tipo_accion} - {self.fecha_hora}"
