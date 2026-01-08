import os
import sys
# Ensure project root is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','core.settings')
import django
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model
from caja.models import Caja
from auditoria.models import Actividad

User = get_user_model()
user = User.objects.first()
print('user:', user.username)
client = Client()
client.force_login(user)

# Open a new caja via POST
resp = client.post('/caja/abrir/', {'monto_inicial': '500.00'})
print('/caja/abrir/ status:', resp.status_code)
ultima_caja = Caja.objects.filter(abierta=True).order_by('-hora_apertura').first()
print('Caja abierta id:', ultima_caja.id)

# Create a product via the web view
from inventario.models import Categoria
cat = Categoria.objects.first()
if not cat:
    cat = Categoria.objects.create(nombre='GEN')

resp = client.post('/inventario/productos/nuevo/', {
    'codigo_barra': 'ACT100',
    'nombre': 'ProductoAct',
    'categoria': cat.id,
    'tipo_producto': 'UNITARIO',
    'unidad_base': 'UNIDAD',
    'stock_actual_base': '10',
    'stock_minimo': '1',
    'precio_compra': '1.00',
    'precio_venta': '2.00',
    'activo': 'on'
})
print('/inventario/productos/nuevo/ status:', resp.status_code)

# Run management command to add ventas grandes (creates two ventas)
from django.core.management import call_command
call_command('add_ventas_large')

# Check activities for the latest opened caja
actividades = Actividad.objects.filter(caja=ultima_caja).order_by('-fecha_hora')
for a in actividades:
    print(a.fecha_hora, a.tipo_accion, a.usuario.username, a.descripcion)

# Fetch home page and print snippet
resp = client.get('/')
content = resp.content.decode('utf-8')
start = content.find('Últimas Actividades')
snippet = content[start:start+400]
print('Home snippet:', snippet)
