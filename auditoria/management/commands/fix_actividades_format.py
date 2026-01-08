from django.core.management.base import BaseCommand
from auditoria.models import Actividad
import re
from inventario.templatetags.format_numbers import format_money


class Command(BaseCommand):
    help = 'Fix formatting of monetary amounts in Actividad.descripcion for VENTA/CIERRE_CAJA/APERTURA_CAJA'

    def handle(self, *args, **options):
        qs = Actividad.objects.filter(tipo_accion__in=['VENTA', 'CIERRE_CAJA', 'APERTURA_CAJA'])
        if not qs.exists():
            self.stdout.write('No matching actividades found')
            return

        venta_re = re.compile(r'(Venta\s+\d+\s+total\s+\$)(\d+(?:\.\d+)?)', re.IGNORECASE)
        cierre_re = re.compile(r'(Total vendido:\s*\$)(\d+(?:\.\d+)?)', re.IGNORECASE)
        apertura_re = re.compile(r'(monto inicial\s*\$)(\d+(?:\.\d+)?)', re.IGNORECASE)

        updated = 0
        for a in qs:
            orig = a.descripcion
            new = orig

            def _fmt(match):
                prefix = match.group(1)
                amount = match.group(2)
                try:
                    fmt = format_money(amount)
                except Exception:
                    fmt = amount
                return f"{prefix}{fmt}"

            new = venta_re.sub(_fmt, new)
            new = cierre_re.sub(_fmt, new)
            new = apertura_re.sub(_fmt, new)

            if new != orig:
                a.descripcion = new
                a.save()
                updated += 1
                self.stdout.write(f'Updated Actividad id={a.id}: "{orig}" -> "{new}"')

        self.stdout.write(f'Done. Updated {updated} actividades.')
