from django.db.models.signals import post_save
from django.dispatch import receiver
from ventas.models import Venta
from .models import Actividad
from inventario.templatetags.format_numbers import format_money, format_decimal
from inventario.models import Producto
from caja.models import Caja
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import pre_save, post_save, pre_delete
from django.conf import settings
from django.apps import apps
import logging
from decimal import Decimal, InvalidOperation


def _fmt_val(v):
    """Format value for audit output: remove trailing .0 for integers, strip insignificant zeros."""
    if v is None:
        return ''
    s = str(v)
    try:
        d = Decimal(s)
    except Exception:
        return s
    try:
        if d == d.to_integral():
            return str(int(d))
        # normalize removes exponent; format as fixed point without scientific notation
        normalized = format(d.normalize(), 'f')
        return normalized
    except Exception:
        return s

logger = logging.getLogger(__name__)
logger.info("auditoria.signals module imported")

# Cache to hold previous DB state between pre_save and post_save
_pre_save_cache = {}


def _should_audit(sender):
    # Avoid auditing internal Django models and the Actividad model itself
    app_label = sender._meta.app_label
    model_name = sender.__name__
    # NOTE: 'migrations' corresponds to django_migrations.Migration; auditing it can break migrate/test DB setup
    if app_label in ('admin', 'contenttypes', 'sessions', 'auth', 'migrations'):
        return False
    if model_name == 'Actividad':
        return False
    # IngresoStock already has a dedicated, human-friendly INGRESO_STOCK audit entry.
    # Auditing the header + each detail as generic "CREACION_REGISTRO" is noisy in UI.
    if app_label == 'inventario' and model_name.lower() in ('ingresostock', 'ingresostockdetalle'):
        return False
    return True


def _get_default_user_and_caja():
    # Try to pick a sensible user and caja for the activity (non-fatal)
    try:
        caja = Caja.objects.filter(abierta=True).order_by('-hora_apertura').first()
    except Exception:
        caja = None
    try:
        if caja and getattr(caja, 'abierta_por', None):
            user = caja.abierta_por
        else:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    except Exception:
        user = None
    # Final fallback: ensure we return some User object if possible
    if user is None:
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.first()
        except Exception:
            user = None
    return user, caja


@receiver(pre_save)
def _capture_old_instance(sender, instance, **kwargs):
    if not _should_audit(sender):
        return
    try:
        logger.debug("_capture_old_instance called for %s id=%s", sender, getattr(instance, 'pk', None))
        pk = getattr(instance, 'pk', None)
        if pk is None:
            return
        # read current DB values for comparison later
        old = sender.objects.filter(pk=pk).values().first()
        if old:
            _pre_save_cache[(sender.__name__, pk)] = old
    except Exception:
        logger.exception("Error in _capture_old_instance for %s", sender)
        pass


@receiver(post_save)
def _audit_changes(sender, instance, created, **kwargs):
    if not _should_audit(sender):
        return
    try:
        logger.debug("_audit_changes called for %s id=%s created=%s", sender, getattr(instance, 'pk', None), created)
        model_label = sender.__name__
        user, caja = _get_default_user_and_caja()
        if created:
            # Log creation, prefer model-specific category action for Categoria
            # Skip generic creation audit for Caja (specific APERTURA_CAJA is recorded in view)
            if getattr(sender._meta, 'app_label', '') == 'caja' and sender.__name__.lower() == 'caja':
                logger.debug("Skipping generic creation audit for Caja id=%s", getattr(instance, 'pk', None))
                return
            # Skip generic creation audit for VentaDetalle (ventas app uses Venta receiver and details are noisy)
            if getattr(sender._meta, 'app_label', '') == 'ventas' and sender.__name__.lower() == 'ventadetalle':
                logger.debug("Skipping generic creation audit for VentaDetalle id=%s", getattr(instance, 'pk', None))
                return
            # Skip generic creation audit for Venta (ventas app already records a nicer VENTA activity)
            if getattr(sender._meta, 'app_label', '') == 'ventas' and sender.__name__.lower() == 'venta':
                logger.debug("Skipping generic creation audit for Venta id=%s", getattr(instance, 'pk', None))
                return

            if getattr(sender._meta, 'app_label', '') == 'inventario' and sender.__name__.lower() == 'categoria':
                tipo = 'CREACION_CATEGORIA'
                # Include the category name when available
                try:
                    nombre = getattr(instance, 'nombre', None)
                    descr = f'Categoría creada: {nombre}' if nombre else f'Creado {model_label} id={getattr(instance, "pk", None)}'
                except Exception:
                    descr = f'Creado {model_label} id={getattr(instance, "pk", None)}'
            elif getattr(sender._meta, 'app_label', '') == 'inventario' and sender.__name__.lower() == 'producto':
                tipo = 'CREACION_PRODUCTO'
                try:
                    nombre = getattr(instance, 'nombre', None)
                    descr = f'Producto creado: {nombre}' if nombre else f'Creado {model_label} id={getattr(instance, "pk", None)}'
                except Exception:
                    descr = f'Creado {model_label} id={getattr(instance, "pk", None)}'
            else:
                tipo = 'CREACION_REGISTRO'
                descr = f'Creado {model_label} id={getattr(instance, "pk", None)}'
            try:
                Actividad.objects.create(
                    usuario=user or getattr(instance, 'usuario', None) or user,
                    tipo_accion=tipo,
                    descripcion=descr,
                    caja=caja
                )
            except Exception:
                logger.exception("Failed to create Actividad for creation of %s (tipo=%s) desc=%s", model_label, tipo, descr)
            return

        key = (sender.__name__, getattr(instance, 'pk', None))
        old = _pre_save_cache.pop(key, None)
        # Skip generic update audits for Caja model because caja views create specific activities (APERTURA/CIERRE)
        if getattr(sender._meta, 'app_label', '') == 'caja' and sender.__name__.lower() == 'caja':
            logger.debug("Skipping generic audit for caja model %s id=%s", sender, getattr(instance, 'pk', None))
            return
        if not old:
            # No previous state captured; log and return
            logger.debug("No previous state cached for %s id=%s", sender, getattr(instance, 'pk', None))
            return
        changes = []
        # Fields to always ignore (timestamps, auto fields)
        IGNORE_FIELDS = {'updated_at', 'created_at'}
        for field, old_val in old.items():
            # skip internal fields
            if field in ('id',) or field in IGNORE_FIELDS:
                continue
            # New value from instance: values() returns DB column names (FKs as field_id), so getattr should match
            try:
                new_val = getattr(instance, field)
            except Exception:
                # fallback to attribute with _id for relations
                try:
                    new_val = getattr(instance, f"{field}_id")
                except Exception:
                    new_val = None

            # If both are None or equal, skip
            if old_val is None and new_val is None:
                continue

            # Try numeric normalization to avoid false positives like '1001.0' vs '1001'
            old_str = str(old_val) if old_val is not None else ''
            new_str = str(new_val) if new_val is not None else ''
            numeric_equal = False
            try:
                old_dec = Decimal(old_str)
                new_dec = Decimal(new_str)
                if old_dec == new_dec:
                    numeric_equal = True
            except (InvalidOperation, TypeError):
                numeric_equal = False

            if numeric_equal:
                continue

            # if string representation identical, skip
            if old_str == new_str:
                continue

            changes.append(f"{field}: '{old_str}' -> '{new_str}'")

        if changes:
            # Determine acting user display
            acting_user = None
            try:
                acting_user = user or getattr(instance, 'usuario', None)
            except Exception:
                acting_user = user
            user_label = f" por {acting_user.username}" if getattr(acting_user, 'username', None) else ''

            # Special formatting for Categoria to show human-friendly field names
            if getattr(sender._meta, 'app_label', '') == 'inventario' and sender.__name__.lower() == 'categoria':
                # Map model fields to readable labels
                field_map = {
                    'nombre': 'Nombre',
                    'descripcion': 'Descripción',
                }
                # Obtain old nombre to show in parentheses (fall back to current instance.nombre)
                try:
                    old_nombre = old.get('nombre') if old and isinstance(old, dict) else None
                except Exception:
                    old_nombre = None
                if not old_nombre:
                    old_nombre = getattr(instance, 'nombre', None) or ''

                parts_readable = []
                new_nombre = None
                for ch in changes:
                    # changes are like "field: 'old' -> 'new'"
                    parts = ch.split(':', 1)
                    if len(parts) == 2:
                        field = parts[0].strip()
                        rest = parts[1].strip()
                        # rest: "'old' -> 'new'"
                        if '->' in rest:
                            old_part, new_part = rest.split('->', 1)
                            old_val = old_part.strip().strip("'\" ")
                            new_val = new_part.strip().strip("'\" ")
                        else:
                            # fallback if unexpected format
                            continue
                        # Ensure order is old = new by checking instance value
                        try:
                            inst_val = getattr(instance, field)
                            inst_str = str(inst_val) if inst_val is not None else ''
                        except Exception:
                            try:
                                inst_str = str(getattr(instance, f"{field}_id"))
                            except Exception:
                                inst_str = ''
                        # If instance contains the old_val, swap so left is old and right is new
                        if inst_str == old_val:
                            # instance still holds old value, so swap
                            tmp_old, tmp_new = old_val, new_val
                        else:
                            tmp_old, tmp_new = old_val, new_val
                        # track new nombre when changed
                        if field == 'nombre':
                            new_nombre = tmp_new
                        label = field_map.get(field, field)
                        # Format as: Field : old = new (formatted)
                        parts_readable.append(f"{label} : {_fmt_val(tmp_old)} = {_fmt_val(tmp_new)}")
                    else:
                        parts_readable.append(ch.replace('->', '='))

                # Use the new nombre (if changed) or current instance.nombre
                display_nombre = new_nombre or getattr(instance, 'nombre', '') or ''
                descr = f"Categoria editada ({display_nombre}) : " + '; '.join(parts_readable)
                tipo = 'EDICION_CATEGORIA'
            # Special formatting for Producto to show human-friendly field names
            elif getattr(sender._meta, 'app_label', '') == 'inventario' and sender.__name__.lower() == 'producto':
                # If a Venta activity was created very recently, the product change was likely caused by a sale.
                # In that case, avoid creating an EDICION_PRODUCTO audit to prevent noisy entries.
                try:
                    recent_window = timezone.now() - timedelta(seconds=5)
                    recent_venta = Actividad.objects.filter(tipo_accion='VENTA', fecha_hora__gte=recent_window).exists()
                    if recent_venta:
                        logger.debug("Skipping EDICION_PRODUCTO for producto id=%s due to recent VENTA activity", getattr(instance, 'pk', None))
                        return
                except Exception:
                    # If detection fails, proceed with normal audit
                    pass
                field_map = {
                    'nombre': 'Nombre',
                    'categoria_id': 'Categoría',
                    'categoria': 'Categoría',
                    'tipo_producto': 'Tipo',
                    'unidad_base': 'Unidad',
                    'stock_minimo': 'Stock Mínimo',
                    'stock_actual_base': 'Stock',
                    'precio_compra': 'Precio Compra',
                    'precio_venta': 'Precio Venta',
                    'margen_ganancia': 'Margen',
                    'activo': 'Activo',
                }
                # get old name if present
                try:
                    old_nombre = old.get('nombre') if old and isinstance(old, dict) else None
                except Exception:
                    old_nombre = None
                if not old_nombre:
                    old_nombre = getattr(instance, 'nombre', None) or ''

                parts_readable = []
                new_nombre = None
                for ch in changes:
                    parts = ch.split(':', 1)
                    if len(parts) == 2:
                        field = parts[0].strip()
                        rest = parts[1].strip()
                        if '->' in rest:
                            old_part, new_part = rest.split('->', 1)
                            old_val = old_part.strip().strip("'\" ")
                            new_val = new_part.strip().strip("'\" ")
                        else:
                            continue
                        # normalize field key for mapping (values() may return fk as field_id)
                        map_field = field
                        if field.endswith('_id'):
                            map_field = field
                        # track nombre change
                        if field == 'nombre':
                            new_nombre = new_val
                        label = field_map.get(map_field, field)
                        parts_readable.append(f"{label} : {_fmt_val(old_val)} = {_fmt_val(new_val)}")
                    else:
                        parts_readable.append(ch.replace('->', '='))

                display_nombre = new_nombre or getattr(instance, 'nombre', '') or ''
                descr = f"Producto editado ({display_nombre}) : " + '; '.join(parts_readable)
                tipo = 'EDICION_PRODUCTO'
            else:
                descr = f'Actualización {model_label} id={getattr(instance, "pk", None)}{user_label}: ' + '; '.join(changes)
                tipo = 'EDICION_REGISTRO'

            try:
                Actividad.objects.create(
                    usuario=acting_user if acting_user is not None else user,
                    tipo_accion=tipo,
                    descripcion=descr,
                    caja=caja
                )
            except Exception:
                logger.exception("Failed to create Actividad for update of %s id=%s desc=%s", model_label, getattr(instance, 'pk', None), descr)
    except Exception:
        # Never raise from auditing
        logger.exception("Unhandled error in _audit_changes for %s", sender)
        pass


@receiver(pre_delete)
def _audit_delete(sender, instance, **kwargs):
    if not _should_audit(sender):
        return
    try:
        model_label = sender.__name__
        user, caja = _get_default_user_and_caja()
        # collect field values
        data = {}
        for field in instance._meta.concrete_fields:
            try:
                val = getattr(instance, field.name)
            except Exception:
                val = None
            data[field.name] = val
        # For Categoria use specific tipo and concise message
        if getattr(sender._meta, 'app_label', '') == 'inventario' and sender.__name__.lower() == 'categoria':
            parts = [f"{k}='{v}'" for k, v in data.items() if k in ('nombre', 'descripcion') and k != 'id']
            descr = f'Categoría eliminada id={getattr(instance, "pk", None)}: ' + '; '.join(parts)
            tipo = 'ELIMINACION_CATEGORIA'
        else:
            parts = [f"{k}='{v}'" for k, v in data.items() if k != 'id']
            descr = f'Eliminado {model_label} id={getattr(instance, "pk", None)}: ' + '; '.join(parts)
            tipo = 'ELIMINACION_REGISTRO'

        try:
            Actividad.objects.create(
                usuario=user or getattr(instance, 'usuario', None) or user,
                tipo_accion=tipo,
                descripcion=descr,
                caja=caja
            )
        except Exception:
            logger.exception("Failed to create Actividad for delete of %s id=%s desc=%s", model_label, getattr(instance, 'pk', None), descr)
    except Exception:
        logger.exception("Unhandled error in _audit_delete for %s", sender)
        pass


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
                    actual_display = f"{format_decimal(parts[0])} {parts[1]}"
                else:
                    actual_display = format_decimal(sd)
            except Exception:
                actual_display = format_decimal(producto.stock_actual_base)

            try:
                smd = producto.stock_minimo_display
                if isinstance(smd, str) and ' ' in smd:
                    parts = smd.rsplit(' ', 1)
                    minimo_display = f"{format_decimal(parts[0])} {parts[1]}"
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
                    # Evitar duplicados: actividad similar en la misma caja en la última hora
                    one_hour_ago = timezone.now() - timedelta(hours=1)
                    qs = Actividad.objects.filter(tipo_accion='STOCK_BAJO', descripcion__icontains=prod_name, fecha_hora__gte=one_hour_ago)
                    if caja:
                        qs = qs.filter(caja=caja)
                    if not qs.exists():
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