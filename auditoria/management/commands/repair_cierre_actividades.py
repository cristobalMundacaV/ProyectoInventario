from django.core.management.base import BaseCommand
from auditoria.models import Actividad
from caja.models import Caja
from inventario.templatetags.format_numbers import format_money
import re


class Command(BaseCommand):
    help = 'Repair CIERRA_CAJA actividad descriptions using Caja.total_vendido'

    def handle(self, *args, **options):
        qs = Actividad.objects.filter(tipo_accion='CIERRE_CAJA')
        if not qs.exists():
            self.stdout.write('No CIERRA_CAJA actividades found')
            return

        updated = 0
        for a in qs:
            # Attempt to find associated caja id from the FK or from text
            caja_id = a.caja_id
            if not caja_id:
                # try to parse numeric after 'Caja' or similar (fallback)
                m = re.search(r'caja\s*(\d+)', (a.descripcion or ''), re.IGNORECASE)
                if m:
                    caja_id = int(m.group(1))

            if not caja_id:
                continue

            try:
                c = Caja.objects.get(pk=caja_id)
            except Caja.DoesNotExist:
                continue

            try:
                total_fmt = format_money(c.total_vendido)
            except Exception:
                total_fmt = str(c.total_vendido)

            new_descr = f'Caja cerrada. Total vendido: ${total_fmt}'
            if a.descripcion != new_descr:
                a.descripcion = new_descr
                a.save()
                updated += 1
                self.stdout.write(f'Updated actividad id={a.id} -> {new_descr!r}')

        self.stdout.write(f'Done. Updated {updated} actividades.')
