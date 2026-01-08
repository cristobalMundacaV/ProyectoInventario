from django.core.management.base import BaseCommand
from caja.models import Caja


class Command(BaseCommand):
    help = 'Print recent cajas and their totals for debugging'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=20, help='Number of recent cajas to show')

    def handle(self, *args, **options):
        limit = options.get('limit', 20)
        qs = Caja.objects.order_by('-hora_apertura')[:limit]
        if not qs:
            self.stdout.write('No cajas found')
            return

        for c in qs:
            self.stdout.write('---')
            self.stdout.write(f'Caja id={c.id} fecha={c.fecha} abierta={c.abierta} hora_apertura={c.hora_apertura} hora_cierre={c.hora_cierre}')
            self.stdout.write(f'  monto_inicial={c.monto_inicial!r} total_vendido={c.total_vendido!r} total_efectivo={c.total_efectivo!r} total_debito={c.total_debito!r} total_transferencia={c.total_transferencia!r}')

        self.stdout.write('--- End')
