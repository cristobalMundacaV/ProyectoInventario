import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model
from caja.models import Caja
from inventario.models import Categoria, Producto
from ventas.models import Venta
from auditoria.models import Actividad
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

# Prepare
user, created = User.objects.get_or_create(username='trigger_user')
if created:
    user.set_password('x')
    user.save()

client = Client()
client.force_login(user)

# Ensure a caja open
caja = Caja.objects.filter(abierta=True).order_by('-hora_apertura').first()
if not caja:
    caja = Caja.objects.create(fecha=timezone.now().date(), monto_inicial=0, hora_apertura=timezone.now(), abierta_por=user, abierta=True)

# Ensure a product (force values)
cat, _ = Categoria.objects.get_or_create(nombre='TEST')
prod, _ = Producto.objects.get_or_create(
    codigo_barra='TRIG001',
    defaults={
        'nombre': 'Trigger Product',
        'categoria': cat,
        'tipo_producto': 'UNITARIO',
        'unidad_base': 'UNIDAD',
        'stock_actual_base': Decimal('2'),
        'stock_minimo': Decimal('1'),
        'precio_compra': Decimal('1.00'),
        'precio_venta': Decimal('10.00'),
    }
)
# Ensure the product has the desired stock values even if existed
prod.stock_actual_base = Decimal('2')
prod.stock_minimo = Decimal('1')
prod.save()

# Post a sale that consumes 2 units
url = '/ventas/create/'
data = {
    'metodo_pago': 'EFECTIVO',
    'form-TOTAL_FORMS': '1',
    'form-INITIAL_FORMS': '0',
    'form-MIN_NUM_FORMS': '1',
    'form-MAX_NUM_FORMS': '1000',
    'form-0-producto': str(prod.id),
    'form-0-unidad_venta': 'UNIDAD',
    'form-0-cantidad_ingresada': '2',
}

resp = client.post(url, data, follow=True)
print('POST status:', resp.status_code)

# Check activities
acts = Actividad.objects.filter(tipo_accion='STOCK_BAJO').order_by('-fecha_hora')[:10]
print('Recent STOCK_BAJO:')
for a in acts:
    print(a.id, a.fecha_hora, a.descripcion, 'usuario=', a.usuario.username if a.usuario else None, 'caja=', a.caja_id)

# Also print latest Venta
new_v = Venta.objects.order_by('-fecha').first()
print('New Venta:', new_v.id if new_v else None)
