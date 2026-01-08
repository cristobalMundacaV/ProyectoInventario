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
user, created = User.objects.get_or_create(username='retry_user')
if created:
    user.set_password('x')
    user.save()

client = Client()
client.force_login(user)

# Ensure a caja open
caja = Caja.objects.filter(abierta=True).order_by('-hora_apertura').first()
if not caja:
    caja = Caja.objects.create(fecha=timezone.now().date(), monto_inicial=0, hora_apertura=timezone.now(), abierta_por=user, abierta=True)

# Ensure a product
cat, _ = Categoria.objects.get_or_create(nombre='TRY')
prod, _ = Producto.objects.get_or_create(
    codigo_barra='RETRY001',
    defaults={
        'nombre': 'Retry Product',
        'categoria': cat,
        'tipo_producto': 'UNITARIO',
        'unidad_base': 'UNIDAD',
        'stock_actual_base': Decimal('100'),
        'stock_minimo': Decimal('0'),
        'precio_compra': Decimal('1.00'),
        'precio_venta': Decimal('10.00'),
    }
)

before_ventas = Venta.objects.count()
before_actividades = Actividad.objects.filter(tipo_accion='VENTA', caja=caja).count()

url = '/ventas/create/'
# Simulate form submission as the UI will send
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

after_ventas = Venta.objects.count()
print('Ventas before:', before_ventas, 'after:', after_ventas)
new_v = Venta.objects.order_by('-fecha').first()
if new_v:
    print('New Venta id:', new_v.id, 'total:', new_v.total, 'caja:', new_v.caja.id)

after_actividades = Actividad.objects.filter(tipo_accion='VENTA', caja=caja).count()
print('Actividades de VENTA before:', before_actividades, 'after:', after_actividades)
if new_v:
    acts = Actividad.objects.filter(tipo_accion='VENTA', descripcion__icontains=f'Venta {new_v.id}')
    for a in acts:
        print('Actividad:', a.id, a.descripcion, 'usuario:', a.usuario.username, 'caja:', a.caja.id if a.caja else None)
