import os
import django
import json
import sys

# Ajustar el módulo de settings del proyecto
# Asegurar que el proyecto está en sys.path
import sys
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    django.setup()
except Exception as e:
    print('ERROR al inicializar Django:', e)
    sys.exit(1)

from django.test import Client
from inventario.models import Categoria, Producto
from decimal import Decimal
from django.contrib.auth import get_user_model

# Crear o recuperar categoría de prueba
cat, _ = Categoria.objects.get_or_create(nombre='TEST-CAT')

# Crear producto de prueba (si ya existe, actualizar stock)
codigo = 'TEST-CODE-123'
producto, created = Producto.objects.get_or_create(
    codigo_barra=codigo,
    defaults={
        'nombre': 'Producto Test Ajax',
        'categoria': cat,
        'tipo_producto': 'UNITARIO',
        'unidad_base': 'UNIDAD',
        'stock_actual_base': Decimal('10'),
        'stock_minimo': Decimal('1'),
        'precio_compra': Decimal('100'),
        'precio_venta': Decimal('150'),
    }
)
if not created:
    producto.stock_actual_base = Decimal('10')
    producto.precio_venta = Decimal('150')
    producto.save()

client = Client()
# Crear usuario de prueba y loguear
User = get_user_model()
username = 'testajax'
password = 'testpass123'
user, ucreated = User.objects.get_or_create(username=username)
if ucreated:
    user.set_password(password)
    user.save()
logged = client.login(username=username, password=password)
print('LOGGED IN:', logged)
payload = {'codigo': codigo, 'cantidad': 2}
resp = client.post('/ventas/agregar-producto/', json.dumps(payload), content_type='application/json')
print('STATUS:', resp.status_code)
# Intentar imprimir JSON bonito
try:
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
except Exception:
    print('RESPONSE:', resp.content)
