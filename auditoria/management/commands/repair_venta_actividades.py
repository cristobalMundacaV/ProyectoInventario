from django.core.management.base import BaseCommand
from auditoria.models import Actividad
from ventas.models import Venta
import re
from inventario.templatetags.format_numbers import format_money


class Command(BaseCommand):
    help = 'Repair Actividad.descripcion for VENTA entries by looking up Venta.total from DB'

    def handle(self, *args, **options):
        qs = Actividad.objects.filter(tipo_accion='VENTA')
        venta_re = re.compile(r'(Venta\s+)(\d+)(\s+total\s+\$)([\d\.]+)', re.IGNORECASE)
        updated = 0
        for a in qs:
            m = venta_re.search(a.descripcion or '')
            if not m:
                continue
            venta_id = int(m.group(2))
            try:
                v = Venta.objects.get(pk=venta_id)
            except Venta.DoesNotExist:
                continue
            try:
                total_fmt = format_money(v.total)
            except Exception:
                total_fmt = str(v.total)

            new_descr = venta_re.sub(lambda mo: f"{mo.group(1)}{mo.group(2)}{mo.group(3)}{total_fmt}", a.descripcion)
            if new_descr != a.descripcion:
                a.descripcion = new_descr
                a.save()
                updated += 1
                self.stdout.write(f'Updated actividad id={a.id} -> {new_descr!r}')

        self.stdout.write(f'Done. Updated {updated} actividades.')
