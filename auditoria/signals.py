from django.db.models.signals import post_save
from django.dispatch import receiver
from ventas.models import Venta
from .models import Actividad
from inventario.templatetags.format_numbers import format_money, format_decimal
from inventario.models import Producto
from caja.models import Caja
from django.utils import timezone
from datetime import timedelta


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


@receiver(post_save, sender=Producto)
def producto_post_save(sender, instance, created, **kwargs):
    """Crear una actividad 'STOCK_BAJO' cuando el stock del producto quede <= stock_minimo.
    Evitamos duplicados creando una actividad similar en la misma caja en la última hora.
    """
    try:
        producto = instance
        if producto.stock_minimo is None or producto.stock_actual_base is None:
            return

        if producto.stock_actual_base <= producto.stock_minimo:
            prod_name = str(producto.nombre).lower()
            try:
                sd = producto.stock_display
                if isinstance(sd, str) and ' ' in sd:
                    parts = sd.rsplit(' ', 1)
                    sd_num = format_decimal(parts[0])
                    actual_display = f"{sd_num} {parts[1]}"
                else:
                    actual_display = format_decimal(sd)
            except Exception:
                actual_display = format_decimal(producto.stock_actual_base)
            try:
                smd = producto.stock_minimo_display
                if isinstance(smd, str) and ' ' in smd:
                    parts = smd.rsplit(' ', 1)
                    smd_num = format_decimal(parts[0])
                    minimo_display = f"{smd_num} {parts[1]}"
                else:
                    minimo_display = format_decimal(smd)
            except Exception:
                minimo_display = format_decimal(producto.stock_minimo)
                descr = f'Stock bajo: {prod_name} = {actual_display} (mínimo {minimo_display})'
                    caja = Caja.objects.filter(abierta=True).order_by('-hora_apertura').first()
                    try:
                        # Determinar usuario para la actividad: preferir el que abrió la caja, si no, buscar un usuario válido
                        user = None
                        if caja and getattr(caja, 'abierta_por', None):
                            user = caja.abierta_por
                        else:
                            from django.contrib.auth import get_user_model
                            User = get_user_model()
                            user = User.objects.filter(is_superuser=True).first() or User.objects.first()

                        if user:
                            Actividad.objects.create(
                                usuario=user,
                                tipo_accion='STOCK_BAJO',
                                descripcion=descr,
                                caja=caja
                            )
                    except Exception:
                        # No queremos que un fallo en auditoría rompa la operación que salvó el producto
                        pass
    except Exception:
        pass