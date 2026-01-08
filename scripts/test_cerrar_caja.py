from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()
user = User.objects.first()
if not user:
    user = User.objects.create_user('testuser', 'test@example.com', 'testpass')
print('user:', user.username)

from caja.models import Caja
from inventario.models import Producto, Categoria
from ventas.models import Venta, VentaDetalle

now = timezone.now()
caja = Caja.objects.create(fecha=now.date(), monto_inicial=Decimal('100.00'), hora_apertura=now, abierta_por=user)
print('Caja creada:', caja.id)

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
print('Producto1:', p1.id, 'margen_ganancia:', p1.margen_ganancia)

v1 = Venta.objects.create(total=Decimal('20.00'), metodo_pago='EFECTIVO', usuario=user, caja=caja)
VentaDetalle.objects.create(venta=v1, producto=p1, cantidad_ingresada=Decimal('2'), unidad_venta='UNIDAD', cantidad_base=Decimal('2'), precio_unitario=p1.precio_venta, subtotal=Decimal('20.00'))

v2 = Venta.objects.create(total=Decimal('15.00'), metodo_pago='DEBITO', usuario=user, caja=caja)
VentaDetalle.objects.create(venta=v2, producto=p1, cantidad_ingresada=Decimal('1.5'), unidad_venta='UNIDAD', cantidad_base=Decimal('1.5'), precio_unitario=p1.precio_venta, subtotal=Decimal('15.00'))

print('Ventas creadas:', v1.id, v2.id)

from django.test import Client
c = Client()
c.force_login(user)
resp = c.get('/caja/cerrar/')
print('Cerrar status:', resp.status_code)

caja.refresh_from_db()
print('Caja totals:', caja.total_vendido, caja.total_efectivo, caja.total_debito, caja.total_transferencia, caja.ganancia_diaria)
print('Hora cierre:', caja.hora_cierre, 'cerrada_por:', caja.cerrada_por.username if caja.cerrada_por else None)
