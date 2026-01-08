from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal

from caja.models import Caja
from inventario.models import Producto, Categoria
from ventas.models import Venta, VentaDetalle
from django.test import Client


class Command(BaseCommand):
    help = 'Test cierre de caja: crea caja, ventas y llama a cerrar_caja view'

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.first()
        if not user:
            user = User.objects.create_user('testuser', 'test@example.com', 'testpass')
        self.stdout.write(f'user: {user.username}')

        now = timezone.now()
        caja = Caja.objects.create(fecha=now.date(), monto_inicial=Decimal('100.00'), hora_apertura=now, abierta_por=user)
        self.stdout.write(f'Caja creada: {caja.id}')

        cat = Categoria.objects.first()
        if not cat:
            cat = Categoria.objects.create(nombre='GEN')

        p1 = Producto.objects.create(
            nombre='ProdA',
            categoria=cat,
            tipo_producto='UNITARIO',
            unidad_base='UNIDAD',
            stock_actual_base=Decimal('10'),
            precio_compra=Decimal('5.00'),
            precio_venta=Decimal('10.00')
        )
        self.stdout.write(f'Producto1: {p1.id} margen_ganancia: {p1.margen_ganancia}')

        v1 = Venta.objects.create(total=Decimal('20.00'), metodo_pago='EFECTIVO', usuario=user, caja=caja)
        VentaDetalle.objects.create(venta=v1, producto=p1, cantidad_ingresada=Decimal('2'), unidad_venta='UNIDAD', cantidad_base=Decimal('2'), precio_unitario=p1.precio_venta, subtotal=Decimal('20.00'))

        v2 = Venta.objects.create(total=Decimal('15.00'), metodo_pago='DEBITO', usuario=user, caja=caja)
        VentaDetalle.objects.create(venta=v2, producto=p1, cantidad_ingresada=Decimal('1.5'), unidad_venta='UNIDAD', cantidad_base=Decimal('1.5'), precio_unitario=p1.precio_venta, subtotal=Decimal('15.00'))

        self.stdout.write(f'Ventas creadas: {v1.id} {v2.id}')

        c = Client()
        c.force_login(user)
        resp = c.get('/caja/cerrar/')
        self.stdout.write(f'Cerrar status: {resp.status_code}')

        caja.refresh_from_db()
        self.stdout.write('Caja totals:')
        self.stdout.write(f'  total_vendido: {caja.total_vendido}')
        self.stdout.write(f'  total_efectivo: {caja.total_efectivo}')
        self.stdout.write(f'  total_debito: {caja.total_debito}')
        self.stdout.write(f'  total_transferencia: {caja.total_transferencia}')
        self.stdout.write(f'  ganancia_diaria: {caja.ganancia_diaria}')
        self.stdout.write(f'  hora_cierre: {caja.hora_cierre} cerrada_por: {caja.cerrada_por.username if caja.cerrada_por else None}')
