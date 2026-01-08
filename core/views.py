from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from inventario.models import Producto
from ventas.models import Venta
from caja.models import Caja
from auditoria.models import Actividad
from django.db.models import Q
from django.utils import timezone
from django.db.models import Count, Sum

def home(request):
    if request.user.is_authenticated:
        # Estadísticas para el dashboard
        hoy = timezone.now().date()
        
        # Ventas desde apertura de caja
        ultima_caja = Caja.objects.filter(abierta=True).order_by('-hora_apertura').first()
        if ultima_caja:
            ventas_hoy = Venta.objects.filter(caja=ultima_caja).count()
            total_ventas = Venta.objects.filter(caja=ultima_caja).aggregate(total_sum=Sum('total'))['total_sum'] or 0
        else:
            ventas_hoy = 0
            # No hay caja abierta: mostrar total 0 (reiniciar total mostrado)
            total_ventas = 0
        
        # Productos con stock bajo
        productos_stock_bajo = Producto.objects.filter(stock_minimo__gt=0).count()
        
        # Estado de caja
        cajas_abiertas_count = Caja.objects.filter(abierta=True).count()
        caja_abierta = cajas_abiertas_count > 0
        
        # Últimas actividades: si hay una caja abierta, mostrar actividades asociadas a la última caja abierta
        if ultima_caja:
            # Obtener las últimas actividades de la caja
            caja_actividades = list(Actividad.objects.filter(caja=ultima_caja).select_related('usuario').order_by('-fecha_hora')[:10])
            # Asegurar que al menos la última alerta STOCK_BAJO aparezca en la lista (si existe)
            ultima_stock_bajo = Actividad.objects.filter(tipo_accion='STOCK_BAJO').select_related('usuario').order_by('-fecha_hora').first()
            if ultima_stock_bajo and ultima_stock_bajo not in caja_actividades:
                # Insertar la alerta al inicio y recortar a 10 items
                caja_actividades.insert(0, ultima_stock_bajo)
                caja_actividades = caja_actividades[:10]
            ultimas_actividades = caja_actividades
        else:
            ultimas_actividades = Actividad.objects.select_related('usuario').order_by('-fecha_hora')[:10]

        context = {
            'ventas_hoy': ventas_hoy,
            'total_ventas': total_ventas,
            'productos_stock_bajo': productos_stock_bajo,
            'caja_abierta': caja_abierta,
            'cajas_abiertas_count': cajas_abiertas_count,
            'ultimas_actividades': ultimas_actividades,
        }
        
        return render(request, 'home.html', context)
    else:
        return redirect('login')
