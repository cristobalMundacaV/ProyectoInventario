from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decimal import Decimal
from urllib.parse import urlencode
from .models import Caja
from .forms import AperturaCajaForm
from auditoria.models import Actividad
from inventario.templatetags.format_numbers import format_money
from django.db.models import Sum, Count
from django.urls import reverse

from core.authz import role_required
from core.roles import Role


def _ventas_por_categoria(caja: Caja):
    """Devuelve breakdown de ventas por categoría para una caja.

    Calcula sobre los subtotales de VentaDetalle (solo ventas, no abonos de fiado).
    Retorna:
      - items: lista de dicts {categoria, total, pct}
      - total: total de ventas considerado
    """
    from django.db.models.functions import Coalesce
    from django.db.models import Value, CharField, DecimalField
    from ventas.models import VentaDetalle

    qs = (
        VentaDetalle.objects
        .filter(venta__caja=caja)
        .values(cat=Coalesce('producto__categoria__nombre', Value('Sin producto'), output_field=CharField()))
        .annotate(total=Coalesce(Sum('subtotal'), Value(0), output_field=DecimalField(max_digits=12, decimal_places=2)))
        .order_by('-total', 'cat')
    )

    total_general = Decimal('0.00')
    rows = []
    for r in qs:
        try:
            total_cat = Decimal(str(r.get('total') or 0))
        except Exception:
            total_cat = Decimal('0.00')
        total_general += total_cat
        rows.append({'categoria': r.get('cat') or 'Sin producto', 'total': total_cat})

    for row in rows:
        if total_general > 0:
            row['pct'] = (row['total'] / total_general) * Decimal('100')
        else:
            row['pct'] = Decimal('0.00')

    return {'items': rows, 'total': total_general}


def _calcular_resumen_caja_en_vivo(caja: Caja):
    """Calcula totales y ganancia usando ventas/detalles actuales.

    Se usa para mostrar el resumen de "hoy" aunque la caja esté abierta,
    ya que los campos agregados (total_vendido/ganancia_diaria) se llenan al cierre.
    """
    ventas = (
        caja.ventas
        .select_related('usuario')
        .prefetch_related('detalles__producto')
        .all()
    )

    total_vendido = Decimal('0.00')
    total_efectivo = Decimal('0.00')
    total_tarjeta = Decimal('0.00')
    total_transferencia = Decimal('0.00')
    ganancia = Decimal('0.00')

    for v in ventas:
        total = Decimal(str(v.total or 0))
        total_vendido += total

        if v.metodo_pago == 'EFECTIVO':
            total_efectivo += total
        elif v.metodo_pago in ('TARJETA', 'DEBITO'):
            # Aceptar registros legacy 'DEBITO'
            total_tarjeta += total
        elif v.metodo_pago == 'TRANSFERENCIA':
            total_transferencia += total

        for det in v.detalles.all():
            producto = det.producto
            if not producto:
                continue

            precio_compra_real = Decimal('0.00')
            try:
                # precio_compra ya se guarda normalizado:
                # - UNITARIO: costo por unidad
                # - GRANEL: costo por kg
                # - PACK vendido por UNIDAD: costo por unidad
                # - PACK vendido por PACK: costo por pack
                precio_compra_real = Decimal(str(producto.precio_compra))
            except Exception:
                precio_compra_real = Decimal(str(producto.precio_compra or 0))

            ganancia += (Decimal(str(det.precio_unitario or 0)) - precio_compra_real) * Decimal(str(det.cantidad_base or 0))

    return {
        'caja': caja,
        'ventas_count': ventas.count(),
        'total_vendido': total_vendido,
        'total_efectivo': total_efectivo,
        'total_tarjeta': total_tarjeta,
        'total_transferencia': total_transferencia,
        'ganancia': ganancia,
    }

@login_required
@role_required(Role.ENCARGADO)
def caja_list(request):
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    estado = request.GET.get('estado', '')  # 'abierta'|'cerrada'|'' (todo)
    page = request.GET.get('page', 1)

    # Mostrar la caja creada más recientemente primero usando hora_apertura (DateTime)
    cajas = Caja.objects.all().order_by('-hora_apertura')

    # Filtrar por rango de fechas
    if fecha_desde:
        try:
            cajas = cajas.filter(fecha__gte=fecha_desde)
        except Exception:
            pass
    if fecha_hasta:
        try:
            cajas = cajas.filter(fecha__lte=fecha_hasta)
        except Exception:
            pass

    # Filtrar por estado
    if estado == 'abierta':
        cajas = cajas.filter(abierta=True)
    elif estado == 'cerrada':
        cajas = cajas.filter(abierta=False)

    # Paginación
    paginator = Paginator(cajas, 50)  # 50 por página
    try:
        cajas = paginator.page(page)
    except PageNotAnInteger:
        cajas = paginator.page(1)
    except EmptyPage:
        cajas = paginator.page(paginator.num_pages)

    # Indica si hay alguna caja abierta para controlar los botones en la plantilla
    cajas_abiertas = Caja.objects.filter(abierta=True).exists()

    filtros = {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'estado': estado,
    }

    return render(request, 'caja/caja_list.html', {'cajas': cajas, 'cajas_abiertas': cajas_abiertas, 'filtros': filtros})


@login_required
@role_required(Role.ENCARGADO)
def reporte_ganancia_diaria(request):
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    qs = Caja.objects.all()
    if fecha_desde:
        try:
            qs = qs.filter(fecha__gte=fecha_desde)
        except Exception:
            pass
    if fecha_hasta:
        try:
            qs = qs.filter(fecha__lte=fecha_hasta)
        except Exception:
            pass

    rows = (
        qs.values('fecha')
        .annotate(
            cajas=Count('id'),
            total_vendido=Sum('total_vendido'),
            ganancia=Sum('ganancia_diaria'),
        )
        .order_by('-fecha')
    )

    totals = qs.aggregate(total_vendido=Sum('total_vendido'), ganancia=Sum('ganancia_diaria'))
    total_vendido_general = totals.get('total_vendido') or Decimal('0.00')
    ganancia_general = totals.get('ganancia') or Decimal('0.00')

    return render(request, 'caja/reporte_ganancia_diaria.html', {
        'rows': rows,
        'filtros': {'fecha_desde': fecha_desde, 'fecha_hasta': fecha_hasta},
        'total_vendido_general': total_vendido_general,
        'ganancia_general': ganancia_general,
    })


@login_required
@role_required(Role.ENCARGADO)
def ganancia_diaria_hoy(request):
    """Resumen de la caja de hoy (no histórico)."""
    hoy = timezone.localdate()
    cajas = Caja.objects.filter(fecha=hoy).order_by('-hora_apertura')

    rows = []
    total_vendido = Decimal('0.00')
    total_efectivo = Decimal('0.00')
    total_tarjeta = Decimal('0.00')
    total_transferencia = Decimal('0.00')
    ganancia = Decimal('0.00')
    ventas_count = 0

    for caja in cajas:
        r = _calcular_resumen_caja_en_vivo(caja)
        rows.append(r)
        total_vendido += r['total_vendido']
        total_efectivo += r['total_efectivo']
        total_tarjeta += r['total_tarjeta']
        total_transferencia += r['total_transferencia']
        ganancia += r['ganancia']
        ventas_count += r['ventas_count']

    return render(request, 'caja/ganancia_diaria_hoy.html', {
        'hoy': hoy,
        'rows': rows,
        'ventas_count': ventas_count,
        'total_vendido': total_vendido,
        'total_efectivo': total_efectivo,
        'total_tarjeta': total_tarjeta,
        'total_transferencia': total_transferencia,
        'ganancia': ganancia,
    })


@login_required
@role_required(Role.ENCARGADO)
def caja_detail(request, pk):
    """Muestra el detalle de una caja: ventas y sus detalles."""
    caja = get_object_or_404(Caja, pk=pk)
    ventas = caja.ventas.select_related('usuario').prefetch_related('detalles__producto').order_by('-fecha')
    return render(request, 'caja/caja_detail.html', {'caja': caja, 'ventas': ventas})

@login_required
@role_required(Role.ENCARGADO)
def abrir_caja(request):
    if request.method == 'POST':
        form = AperturaCajaForm(request.POST)
        if form.is_valid():
            monto_inicial = form.cleaned_data['monto_inicial']
            caja = Caja.objects.create(
                fecha=timezone.now().date(),
                monto_inicial=monto_inicial,
                hora_apertura=timezone.now(),
                abierta_por=request.user
            )
            # Registrar actividad de apertura de caja
            try:
                monto_fmt = format_money(monto_inicial)
            except Exception:
                monto_fmt = str(monto_inicial)

            Actividad.objects.create(
                usuario=request.user,
                tipo_accion='APERTURA_CAJA',
                descripcion=f'Caja abierta con monto inicial ${monto_fmt}',
                caja=caja
            )

            messages.success(request, f'Caja abierta exitosamente con monto inicial de ${monto_fmt}.')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
    else:
        form = AperturaCajaForm()
    
    return render(request, 'caja/apertura_caja.html', {'form': form})

@login_required
@role_required(Role.ENCARGADO)
def confirmar_cerrar_caja(request):
    """Muestra los datos de la caja para confirmación antes de cerrar."""
    cajas_abiertas = Caja.objects.filter(abierta=True).order_by('-hora_apertura')
    
    if not cajas_abiertas.exists():
        messages.info(request, 'No hay cajas abiertas.')
        next_url = request.GET.get('next', 'home')
        return redirect(next_url)
    
    # Preparar datos de cada caja abierta
    cajas_datos = []
    for caja in cajas_abiertas:
        ventas = caja.ventas.all()
        total_vendido = Decimal('0.00')
        total_efectivo = Decimal('0.00')
        total_tarjeta = Decimal('0.00')
        total_transferencia = Decimal('0.00')
        ganancia = Decimal('0.00')
        cantidad_ventas = ventas.count()

        # Abonos de fiados (ingresos en caja)
        cantidad_abonos_fiado = 0
        total_abonos_fiado = Decimal('0.00')

        for v in ventas:
            total_vendido += Decimal(str(v.total))
            if v.metodo_pago == 'EFECTIVO':
                total_efectivo += Decimal(str(v.total))
            elif v.metodo_pago in ('TARJETA', 'DEBITO'):
                # Aceptar tanto el valor actual 'TARJETA' como registros legacy 'DEBITO'
                total_tarjeta += Decimal(str(v.total))
            elif v.metodo_pago == 'TRANSFERENCIA':
                total_transferencia += Decimal(str(v.total))

            # Ganancia por cada detalle: margen * cantidad_base
            for det in v.detalles.all():
                producto = det.producto
                if not producto:
                    continue
                margen = producto.margen_ganancia or 0
                ganancia += Decimal(str(margen)) * Decimal(str(det.cantidad_base))

        ventas_por_categoria = _ventas_por_categoria(caja)

        # Sumar abonos de fiados como ingresos
        try:
            from ventas.models import FiadoAbono

            abonos = FiadoAbono.objects.filter(caja=caja)
            cantidad_abonos_fiado = abonos.count()
            for a in abonos:
                monto = Decimal(str(a.monto))
                total_abonos_fiado += monto
                total_vendido += monto
                if a.metodo_pago == 'EFECTIVO':
                    total_efectivo += monto
                elif a.metodo_pago in ('TARJETA', 'DEBITO'):
                    total_tarjeta += monto
                elif a.metodo_pago == 'TRANSFERENCIA':
                    total_transferencia += monto
        except Exception:
            pass

        cajas_datos.append({
            'caja': caja,
            'cantidad_ventas': cantidad_ventas,
            'cantidad_abonos_fiado': cantidad_abonos_fiado,
            'total_vendido': total_vendido,
            'total_efectivo': total_efectivo,
            'total_tarjeta': total_tarjeta,
            'total_transferencia': total_transferencia,
            'total_abonos_fiado': total_abonos_fiado,
            'ganancia': ganancia,
            'ventas_por_categoria': ventas_por_categoria,
            'ventas': ventas.order_by('-fecha')[:5]  # Últimas 5 ventas
        })
    
    next_url = request.GET.get('next', '')
    return render(request, 'caja/confirmar_cierre.html', {'cajas_datos': cajas_datos, 'next': next_url})

@login_required
@role_required(Role.ENCARGADO)
def cerrar_caja(request):
    if request.method == 'POST':
        cajas_abiertas = Caja.objects.filter(abierta=True)
        
        if cajas_abiertas.exists():
            # Cerrar todas las cajas abiertas
            count = cajas_abiertas.count()
            closed_ids = []
            for caja in cajas_abiertas:
                caja.abierta = False
                caja.hora_cierre = timezone.now()
                caja.cerrada_por = request.user

                # Agregar resumen de ventas y cálculo de ganancia
                ventas = caja.ventas.all()
                total_vendido = Decimal('0.00')
                total_efectivo = Decimal('0.00')
                total_tarjeta = Decimal('0.00')
                total_transferencia = Decimal('0.00')
                ganancia = Decimal('0.00')

                for v in ventas:
                    # Debug log: show each venta total to detect scaling issues
                    try:
                        print(f"DEBUG_CIERRE Venta {v.id} total (raw): {v.total}")
                    except Exception:
                        print("DEBUG_CIERRE Venta unknown total")
                    total_vendido += Decimal(str(v.total))
                    if v.metodo_pago == 'EFECTIVO':
                        total_efectivo += Decimal(str(v.total))
                    elif v.metodo_pago in ('TARJETA', 'DEBITO'):
                        # Aceptar tanto el valor actual 'TARJETA' como registros legacy 'DEBITO'
                        total_tarjeta += Decimal(str(v.total))
                    elif v.metodo_pago == 'TRANSFERENCIA':
                        total_transferencia += Decimal(str(v.total))

                    # Ganancia por cada detalle: (precio_venta - precio_compra_real) * cantidad_base
                    for det in v.detalles.all():
                        producto = det.producto
                        if producto:
                            precio_compra_real = Decimal('0.00')
                            
                            if producto.tipo_producto == 'PACK' and producto.unidades_por_pack:
                                # precio_compra ya es costo base (por unidad/por kg/por pack)
                                precio_compra_real = Decimal(str(producto.precio_compra))
                            elif producto.tipo_producto == 'GRANEL' and producto.kg_por_caja:
                                precio_compra_real = Decimal(str(producto.precio_compra))
                            else:
                                precio_compra_real = Decimal(str(producto.precio_compra))
                            
                            ganancia += (Decimal(str(det.precio_unitario)) - precio_compra_real) * Decimal(str(det.cantidad_base))

                # Sumar abonos de fiados como ingresos reales en caja
                try:
                    from ventas.models import FiadoAbono

                    abonos = FiadoAbono.objects.filter(caja=caja)
                    for a in abonos:
                        monto = Decimal(str(a.monto))
                        total_vendido += monto
                        if a.metodo_pago == 'EFECTIVO':
                            total_efectivo += monto
                        elif a.metodo_pago in ('TARJETA', 'DEBITO'):
                            total_tarjeta += monto
                        elif a.metodo_pago == 'TRANSFERENCIA':
                            total_transferencia += monto
                except Exception:
                    pass

                caja.total_vendido = total_vendido
                caja.total_efectivo = total_efectivo
                caja.total_debito = total_tarjeta
                caja.total_transferencia = total_transferencia
                caja.ganancia_diaria = ganancia

                caja.save()

                closed_ids.append(caja.id)

                # Debug: log computed totals
                try:
                    print(f"DEBUG_CIERRE Caja {caja.id} total_vendido (Decimal): {total_vendido}")
                except Exception:
                    print("DEBUG_CIERRE Caja total_vendido unknown")

                # Registrar actividad de cierre de caja (formatear total para mostrar miles)
                # Use centralized formatting helper to avoid inconsistencies
                try:
                    total_fmt = format_money(total_vendido)
                except Exception:
                    try:
                        total_fmt = str(int(total_vendido.quantize(Decimal('1'))))
                    except Exception:
                        total_fmt = str(total_vendido)

                Actividad.objects.create(
                    usuario=request.user,
                    tipo_accion='CIERRE_CAJA',
                    descripcion=f'Caja cerrada. Total vendido: ${total_fmt}',
                    caja=caja
                )

            messages.success(request, f'{count} caja(s) cerradas exitosamente.')
            next_url = request.POST.get('next') or request.GET.get('next') or ''

            # Si se cerró solo 1 caja, ir directo a la boleta y abrir el diálogo de impresión.
            if len(closed_ids) == 1:
                url = reverse('caja_boleta', args=[closed_ids[0]])
                params = {'autoprint': 1}
                if next_url:
                    params['next'] = next_url
                return redirect(f"{url}?{urlencode(params)}")

            # Si se cerraron varias, mostrar una pantalla con links de boleta para cada una.
            url = reverse('caja_boletas')
            params = {'ids': ','.join(str(i) for i in closed_ids)}
            if next_url:
                params['next'] = next_url
            return redirect(f"{url}?{urlencode(params)}")
        else:
            messages.info(request, 'No hay cajas abiertas.')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
    else:
        # Si es GET, redirigir a la página de confirmación
        return redirect('confirmar_cerrar_caja')


@login_required
@role_required(Role.ENCARGADO)
def caja_boleta(request, pk):
    caja = get_object_or_404(Caja, pk=pk)

    ventas_por_categoria = _ventas_por_categoria(caja)

    ventas = caja.ventas.all()
    cantidad_ventas = ventas.count()

    cantidad_abonos_fiado = 0
    total_abonos_fiado = Decimal('0.00')
    try:
        from ventas.models import FiadoAbono

        abonos = FiadoAbono.objects.filter(caja=caja)
        cantidad_abonos_fiado = abonos.count()
        total_abonos_fiado = abonos.aggregate(total=Sum('monto')).get('total') or Decimal('0.00')
    except Exception:
        pass

    efectivo_esperado = (caja.monto_inicial or Decimal('0.00')) + (caja.total_efectivo or Decimal('0.00'))

    next_url = request.GET.get('next', '')
    autoprint = request.GET.get('autoprint', '1')

    return render(request, 'caja/boleta_cierre.html', {
        'caja': caja,
        'cantidad_ventas': cantidad_ventas,
        'cantidad_abonos_fiado': cantidad_abonos_fiado,
        'total_abonos_fiado': total_abonos_fiado,
        'efectivo_esperado': efectivo_esperado,
        'ventas_por_categoria': ventas_por_categoria,
        'next': next_url,
        'autoprint': autoprint,
    })


@login_required
@role_required(Role.ENCARGADO)
def caja_boletas(request):
    """Pantalla simple para imprimir boletas cuando se cierran varias cajas a la vez."""
    ids_raw = request.GET.get('ids', '')
    ids = []
    for part in ids_raw.split(','):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))

    cajas = Caja.objects.filter(id__in=ids).order_by('-hora_apertura')
    next_url = request.GET.get('next', '')

    return render(request, 'caja/boletas_cierre.html', {
        'cajas': cajas,
        'next': next_url,
    })
