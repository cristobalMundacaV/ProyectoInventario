from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal

from caja.models import Caja
from inventario.models import Producto, Categoria
from ventas.models import Venta, VentaDetalle


class Command(BaseCommand):
    help = 'Crea dos ventas grandes de 10000: una EFECTIVO y otra DEBITO en la caja abierta (o crea una caja si no existe)'

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.first()
        if not user:
            user = User.objects.create_user('testuser', 'test@example.com', 'testpass')
        self.stdout.write(f'user: {user.username}')

        caja = Caja.objects.filter(abierta=True).first()
        if not caja:
            now = timezone.now()
            caja = Caja.objects.create(fecha=now.date(), monto_inicial=Decimal('0.00'), hora_apertura=now, abierta_por=user)
            self.stdout.write(f'Caja creada: {caja.id}')
        else:
            self.stdout.write(f'Usando caja abierta: {caja.id}')

        # Obtener o crear un producto para usar en los detalles
        producto = Producto.objects.first()
        if not producto:
            cat = Categoria.objects.first()
            if not cat:
                cat = Categoria.objects.create(nombre='GEN')
            producto = Producto.objects.create(
                nombre='ProductoGrande',
                categoria=cat,
                tipo_producto='UNITARIO',
                unidad_base='UNIDAD',
                stock_actual_base=Decimal('10000'),
                precio_compra=Decimal('1.00'),
                precio_venta=Decimal('10.00')
            )
            self.stdout.write(f'Producto creado: {producto.id} precio_venta: {producto.precio_venta}')
        else:
            self.stdout.write(f'Producto usado: {producto.id} precio_venta: {producto.precio_venta}')

        # Calcular cantidad necesaria para alcanzar subtotal 10000
        precio = Decimal(str(producto.precio_venta))
        if precio == 0:
            cantidad_for_10000 = Decimal('1')
        else:
            cantidad_for_10000 = (Decimal('10000') / precio).quantize(Decimal('0.001'))

        # Crear venta EFECTIVO
        v1 = Venta.objects.create(total=Decimal('10000.00'), metodo_pago='EFECTIVO', usuario=user, caja=caja)
        VentaDetalle.objects.create(
            venta=v1,
            producto=producto,
            cantidad_ingresada=cantidad_for_10000,
            unidad_venta='UNIDAD',
            cantidad_base=cantidad_for_10000,
            precio_unitario=precio,
            subtotal=(precio * cantidad_for_10000).quantize(Decimal('0.01'))
        )

        # Crear venta DEBITO
        v2 = Venta.objects.create(total=Decimal('10000.00'), metodo_pago='DEBITO', usuario=user, caja=caja)
        VentaDetalle.objects.create(
            venta=v2,
            producto=producto,
            cantidad_ingresada=cantidad_for_10000,
            unidad_venta='UNIDAD',
            cantidad_base=cantidad_for_10000,
            precio_unitario=precio,
            subtotal=(precio * cantidad_for_10000).quantize(Decimal('0.01'))
        )

        self.stdout.write(f'Ventas creadas: EFECTIVO id={v1.id}, DEBITO id={v2.id}')
        self.stdout.write(f'Cantidad por detalle: {cantidad_for_10000} subtotal calculado: {(precio * cantidad_for_10000).quantize(Decimal("0.01"))}')
