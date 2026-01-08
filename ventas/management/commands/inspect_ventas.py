from django.core.management.base import BaseCommand
from ventas.models import Venta


class Command(BaseCommand):
    help = 'Print recent ventas and their detalle rows for debugging totals'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=20, help='Number of recent ventas to show')

    def handle(self, *args, **options):
        limit = options.get('limit', 20)
        qs = Venta.objects.order_by('-fecha')[:limit]
        if not qs:
            self.stdout.write('No ventas found')
            return

        for v in qs:
            self.stdout.write('---')
            self.stdout.write(f'Venta id={v.id} fecha={v.fecha} caja_id={v.caja_id}')
            self.stdout.write(f'  total (stored): {v.total!r}  type={type(v.total)}')
            detalles = v.detalles.all()
            if not detalles:
                self.stdout.write('  (no detalles)')
            for d in detalles:
                prod = d.producto
                prod_info = f'{prod.id if prod else None} - {getattr(prod, "nombre", None)}'
                self.stdout.write(f'  Detalle id={d.id} producto={prod_info} cantidad_base={d.cantidad_base!r} precio_unitario={d.precio_unitario!r} subtotal={d.subtotal!r}')

        self.stdout.write('--- End')
