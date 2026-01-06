from django.db import models
from core.enums import TipoAccion
from usuarios.models import Usuario


class Actividad(models.Model):
    fecha_hora = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    tipo_accion = models.CharField(max_length=20, choices=TipoAccion.choices)
    descripcion = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Actividades'
