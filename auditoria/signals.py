from django.db.models.signals import post_save
from django.dispatch import receiver
from ventas.models import Venta
from .models import Actividad

@receiver(post_save, sender=Venta)
def venta_creada(sender, instance, created, **kwargs):
    if created:
        caja = instance.caja
        try:
            # Evitar duplicados: si ya existe una actividad correspondiente a esta venta, no crear otra
            descr = f'Venta {instance.id} total ${instance.total} ({instance.metodo_pago})'
            exists = Actividad.objects.filter(tipo_accion='VENTA', caja=caja, descripcion__icontains=f'Venta {instance.id}').exists()
            if not exists:
                Actividad.objects.create(
                    usuario=instance.usuario,
                    tipo_accion='VENTA',
                    descripcion=descr,
                    caja=caja
                )
        except Exception:
            # evitar romper flujos en caso de errores de auditoría
            pass