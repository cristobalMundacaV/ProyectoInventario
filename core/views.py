from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.views.decorators.http import require_http_methods
from inventario.models import Producto
from ventas.models import Venta
from caja.models import Caja
from auditoria.models import Actividad
from django.db.models import Q
from django.utils import timezone
from django.db.models import Count, Sum
from inventario.models import bajo_stock_queryset

@login_required
def home(request):
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
 
    # Productos con stock bajo (lógica unificada)
    productos_stock_bajo = bajo_stock_queryset(Producto.objects.all()).count()
 
    # Estado de caja
    cajas_abiertas_count = Caja.objects.filter(abierta=True).count()
    caja_abierta = cajas_abiertas_count > 0
 
    # Últimas actividades: mostrar las últimas actividades registradas (no depender de caja abierta)
    # Ocultar filas genéricas antiguas (CREACION_REGISTRO) de IngresoStock/IngresoStockDetalle para evitar ruido.
    ultimas_actividades = (
        Actividad.objects.select_related('usuario')
        .exclude(
            Q(tipo_accion='CREACION_REGISTRO')
            & (
                Q(descripcion__startswith='Creado IngresoStockDetalle')
                | Q(descripcion__startswith='Creado IngresoStock')
            )
        )
        .order_by('-fecha_hora')[:10]
    )

    context = {
        'ventas_hoy': ventas_hoy,
        'total_ventas': total_ventas,
        'productos_stock_bajo': productos_stock_bajo,
        'caja_abierta': caja_abierta,
        'cajas_abiertas_count': cajas_abiertas_count,
        'ultimas_actividades': ultimas_actividades,
    }

    return render(request, 'home.html', context)


@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    return redirect('login')
