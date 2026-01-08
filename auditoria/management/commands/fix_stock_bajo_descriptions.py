from django.core.management.base import BaseCommand
import re
from auditoria.models import Actividad
from inventario.models import Producto
from inventario.templatetags.format_numbers import format_decimal


class Command(BaseCommand):
    help = 'Normaliza las descripciones de actividades STOCK_BAJO usando datos actuales del producto'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Aplicar los cambios en la base de datos. Si no se pasa, se hace dry-run.')
        parser.add_argument('--limit', type=int, default=0, help='Limitar el número de actividades procesadas (0 = todas)')

    def handle(self, *args, **options):
        apply_changes = options['apply']
        limit = options['limit']

        qs = Actividad.objects.filter(tipo_accion='STOCK_BAJO').order_by('-fecha_hora')
        if limit > 0:
            qs = qs[:limit]

        if not qs:
            self.stdout.write('No hay actividades STOCK_BAJO para procesar')
            return

        updated = 0
        for a in qs:
            desc = (a.descripcion or '').strip()
            # Try to extract the product name from description
            m = re.search(r'Stock bajo:\s*([^=\-\(]+)', desc, flags=re.IGNORECASE)
            if not m:
                # fallback: look for pattern after 'Stock bajo:' until '(' or end
                m = re.search(r'Stock bajo:\s*(.*?)\s*(?:\(|$)', desc, flags=re.IGNORECASE)
            if not m:
                self.stdout.write(f"SKIP id={a.id} no pude extraer nombre de: {desc!r}")
                continue
            name = m.group(1).strip()
            # Try exact match first, then icontains
            producto = Producto.objects.filter(nombre__iexact=name).first()
            if not producto:
                producto = Producto.objects.filter(nombre__icontains=name).first()
            if not producto:
                self.stdout.write(f"SKIP id={a.id} producto no encontrado para nombre extraido: {name!r}")
                continue

            # Build normalized description
            prod_name = str(producto.nombre).lower()
            # format actual and minimo using format_decimal, preserving units if present
            def _format_display(sd):
                try:
                    if isinstance(sd, str) and ' ' in sd:
                        parts = sd.rsplit(' ', 1)
                        num = format_decimal(parts[0])
                        return f"{num} {parts[1]}"
                    return format_decimal(sd)
                except Exception:
                    return str(sd)

            actual_display = _format_display(producto.stock_display)
            minimo_display = _format_display(producto.stock_minimo_display)

            new_desc = f'Stock bajo: {prod_name} = {actual_display} (mínimo {minimo_display})'

            if desc != new_desc:
                self.stdout.write(f"UPDATE id={a.id} -> {new_desc!r}")
                if apply_changes:
                    a.descripcion = new_desc
                    a.save()
                    updated += 1
            else:
                self.stdout.write(f"OK id={a.id} ya normalizado")

        self.stdout.write(f'Done. Updated {updated} actividades.' if apply_changes else 'Dry-run complete.')
