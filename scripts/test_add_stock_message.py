import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model
from inventario.models import Categoria, Producto
from caja.models import Caja
from decimal import Decimal
from django.utils import timezone

User = get_user_model()
user, created = User.objects.get_or_create(username='msg_test')
if created:
    user.set_password('x')
    user.save()

client = Client()
client.force_login(user)

# Ensure caja
caja = Caja.objects.filter(abierta=True).order_by('-hora_apertura').first()
if not caja:
    caja = Caja.objects.create(fecha=timezone.now().date(), monto_inicial=0, hora_apertura=timezone.now(), abierta_por=user, abierta=True)

# Ensure product
cat, _ = Categoria.objects.get_or_create(nombre='MSG')
prod, _ = Producto.objects.get_or_create(
    codigo_barra='MSG001',
    defaults={
        'nombre': 'Coca Cola',
        'categoria': cat,
        'tipo_producto': 'UNITARIO',
        'unidad_base': 'UNIDAD',
        'stock_actual_base': Decimal('114'),
        'stock_minimo': Decimal('100'),
        'precio_compra': Decimal('1.00'),
        'precio_venta': Decimal('10.00'),
    }
)
# enforce stock
prod.stock_actual_base = Decimal('114')
prod.save()

# Post to add 1 unit
url = '/inventario/productos/anadir-stock/'
data = {
    'producto': str(prod.id),
    'cantidad': '1'
}
resp = client.post(url, data, follow=True)
print('POST status:', resp.status_code)
# Extract messages
# Reconstruct expected message text using same logic as view
from inventario.templatetags.format_numbers import format_decimal
from decimal import Decimal as D
cantidad = D('1')
if prod.tipo_producto == 'GRANEL':
    unidad_label = 'kg'
    stock_unit_label = 'kg'
else:
    unidad_label = 'unidad' if cantidad == D('1') else 'unidades'
    stock_unit_label = 'unidad' if (prod.stock_actual_base == D('1')) else 'unidades'
cantidad_display = format_decimal(cantidad)
stock_display = format_decimal(prod.stock_actual_base)
message_text = f'Se añadió {cantidad_display} {unidad_label} al stock de {prod.nombre}. Stock actual: {stock_display} {stock_unit_label}'
print('Reconstructed message:', message_text)
# Show latest activity
from auditoria.models import Actividad
act = Actividad.objects.order_by('-fecha_hora').filter(tipo_accion='INGRESO_STOCK').first()
print('Last INGRESO_STOCK:', act.descripcion if act else None)

# Show product stock
prod.refresh_from_db()
print('Product stock after:', prod.stock_actual_base)
