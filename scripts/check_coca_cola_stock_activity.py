import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()
from inventario.models import Producto
from auditoria.models import Actividad
from caja.models import Caja
from django.utils import timezone

name = 'Coca Cola'
prod = Producto.objects.filter(nombre__iexact=name).first()
if not prod:
    prod = Producto.objects.filter(nombre__icontains='Coca').first()

print('Producto:', prod.nombre if prod else None)
if prod:
    print('  stock_actual_base =', prod.stock_actual_base)
    print('  stock_minimo =', prod.stock_minimo)
    print('  stock_display =', prod.stock_display)
    print('  stock_minimo_display =', prod.stock_minimo_display)

# Caja abierta
caja = Caja.objects.filter(abierta=True).order_by('-hora_apertura').first()
print('Caja abierta id =', caja.id if caja else None)

# Actividades recientes que mencionen coca
acts = Actividad.objects.filter(descripcion__icontains='coca').order_by('-fecha_hora')[:20]
print('\nActividades con "coca" (últimas 20):')
for a in acts:
    print(a.id, a.fecha_hora, a.tipo_accion, a.descripcion, 'caja=', a.caja_id, 'usuario=', getattr(a.usuario, 'username', None))

# Últimas STOCK_BAJO global
acts2 = Actividad.objects.filter(tipo_accion='STOCK_BAJO').order_by('-fecha_hora')[:10]
print('\nÚltimas STOCK_BAJO (10):')
for a in acts2:
    print(a.id, a.fecha_hora, a.descripcion, 'caja=', a.caja_id, 'usuario=', getattr(a.usuario, 'username', None))

# Mostrar si existe STOCK_BAJO reciente para este producto en la caja actual (última hora)
if prod:
    recent_threshold = timezone.now() - timezone.timedelta(hours=1)
    exists = Actividad.objects.filter(
        tipo_accion='STOCK_BAJO',
        descripcion__icontains=prod.nombre.lower(),
        fecha_hora__gte=recent_threshold,
        caja=caja
    ).exists()
    print('\nExiste STOCK_BAJO reciente para este producto en la caja actual (última hora)?', exists)
