from django.db import models


class Actividad(models.Model):

    TIPO_ACCION_CHOICES = [
        ('APERTURA_CAJA', 'Apertura de Caja'),
        ('CIERRE_CAJA', 'Cierre de Caja'),
        ('VENTA', 'Venta'),
        ('INGRESO_STOCK', 'Ingreso de Stock'),
        ('STOCK_BAJO', 'Stock Bajo'),
        ('CREACION_PRODUCTO', 'Creación de Producto'),
        ('EDICION_PRODUCTO', 'Edición de Producto'),
        ('CREACION_CATEGORIA', 'Creación de Categoría'),
        ('EDICION_CATEGORIA', 'Edición de Categoría'),
        ('ELIMINACION_CATEGORIA', 'Eliminación de Categoría'),
        ('CREACION_REGISTRO', 'Creación de Registro'),
        ('EDICION_REGISTRO', 'Edición de Registro'),
        ('ELIMINACION_REGISTRO', 'Eliminación de Registro'),
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
    caja = models.ForeignKey(
        'caja.Caja',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades'
    )

    def __str__(self):
        return f"{self.tipo_accion} - {self.fecha_hora}"
