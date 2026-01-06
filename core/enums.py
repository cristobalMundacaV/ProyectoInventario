from django.db import models


class TipoProducto(models.TextChoices):
    UNITARIO = 'UNITARIO', 'Unitario'
    PACK = 'PACK', 'Pack'
    GRANEL = 'GRANEL', 'Granel'


class UnidadBase(models.TextChoices):
    UNIDAD = 'UNIDAD', 'Unidad'
    KG = 'KG', 'Kilogramo'


class MetodoPago(models.TextChoices):
    EFECTIVO = 'EFECTIVO', 'Efectivo'
    DEBITO = 'DEBITO', 'Débito'
    TRANSFERENCIA = 'TRANSFERENCIA', 'Transferencia'


class TipoAccion(models.TextChoices):
    CREAR = 'CREAR', 'Crear'
    ACTUALIZAR = 'ACTUALIZAR', 'Actualizar'
    ELIMINAR = 'ELIMINAR', 'Eliminar'
    LOGIN = 'LOGIN', 'Login'


class UnidadVenta(models.TextChoices):
    UNIDAD = 'UNIDAD', 'Unidad'
    CAJA = 'CAJA', 'Caja'
    KG = 'KG', 'Kilogramo'
