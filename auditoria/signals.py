from django.db.models.signals import post_save
from django.dispatch import receiver
from ventas.models import Venta
from .models import Actividad
from inventario.templatetags.format_numbers import format_money

@receiver(post_save, sender=Venta)
def venta_creada(sender, instance, created, **kwargs):
    if created:
        caja = instance.caja
        try:
            # Evitar duplicados: si ya existe una actividad correspondiente a esta venta, no crear otra
            # Use the persisted value from the DB to avoid any in-memory scaling/precision issues.
            try:
                db_total = instance.__class__.objects.filter(pk=instance.pk).values_list('total', flat=True).first()
                total_to_format = db_total if db_total is not None else instance.total
                try:
                    print(f"DEBUG_SIGNAL Venta {instance.id} instance.total={instance.total!r} db_total={db_total!r}")
                except Exception:
                    pass
                total_fmt = format_money(total_to_format)
            except Exception:
                try:
                    total_fmt = format_money(instance.total)
                except Exception:
                    total_fmt = str(instance.total)

            descr = f'Venta {instance.id} total ${total_fmt} ({instance.metodo_pago})'
            exists = Actividad.objects.filter(tipo_accion='VENTA', caja=caja, descripcion__icontains=f'Venta {instance.id}').exists()
            if not exists:
                try:
                    print(f"DEBUG_SIGNAL Creating Actividad for Venta {instance.id} with descripcion={descr}")
                except Exception:
                    pass
                Actividad.objects.create(
                    usuario=instance.usuario,
                    tipo_accion='VENTA',
                    descripcion=descr,
                    caja=caja
                )
        except Exception:
            # evitar romper flujos en caso de errores de auditoría
            pass