from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from inventario.models import Producto
from ventas.models import Venta
from caja.models import Caja
from auditoria.models import Actividad
from django.utils import timezone
from django.db.models import Count, Sum

def home(request):
    if request.user.is_authenticated:
        # Estadísticas para el dashboard
        hoy = timezone.now().date()
        
        # Ventas de hoy
        ventas_hoy = Venta.objects.filter(fecha__date=hoy).count()
        
        # Productos con stock bajo
        productos_stock_bajo = Producto.objects.filter(stock_minimo__gt=0).count()
        
        # Estado de caja
        cajas_abiertas_count = Caja.objects.filter(abierta=True).count()
        caja_abierta = cajas_abiertas_count > 0
        
        # Últimas actividades
        ultimas_actividades = Actividad.objects.select_related('usuario').order_by('-fecha_hora')[:10]
        
        context = {
            'ventas_hoy': ventas_hoy,
            'productos_stock_bajo': productos_stock_bajo,
            'caja_abierta': caja_abierta,
            'cajas_abiertas_count': cajas_abiertas_count,
            'ultimas_actividades': ultimas_actividades,
        }
        
        return render(request, 'home.html', context)
    else:
        return redirect('login')
