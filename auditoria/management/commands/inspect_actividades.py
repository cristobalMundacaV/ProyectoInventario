from django.core.management.base import BaseCommand
from auditoria.models import Actividad


class Command(BaseCommand):
    help = 'Print recent actividades for debugging'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=30, help='Number of recent actividades to show')

    def handle(self, *args, **options):
        limit = options.get('limit', 30)
        qs = Actividad.objects.order_by('-fecha_hora')[:limit]
        if not qs:
            self.stdout.write('No actividades found')
            return
        for a in qs:
            self.stdout.write('---')
            self.stdout.write(f'id={a.id} fecha={a.fecha_hora} tipo={a.tipo_accion} usuario={a.usuario.username if a.usuario else None} caja_id={a.caja_id}')
            self.stdout.write(f'  descripcion: {a.descripcion!r}')
        self.stdout.write('--- End')
