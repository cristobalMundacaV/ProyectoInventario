from decimal import Decimal
from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import get_user_model
import json
from django.utils.safestring import mark_safe
from django.utils import timezone
from datetime import timedelta

from core.enums import MetodoPago, UnidadVenta
from caja.models import Caja
from inventario.models import Producto
from .models import Venta, VentaDetalle
from .forms import VentaForm, VentaDetalleFormSet
from auditoria.models import Actividad
from inventario.templatetags.format_numbers import format_money, format_decimal
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count

from core.authz import role_required
from core.roles import Role



@login_required
@role_required(Role.ENCARGADO)
def venta_list(request):
    # Filtros desde querystring
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    metodo = request.GET.get('metodo', '')
    usuario = request.GET.get('usuario', '')

    ventas = Venta.objects.all().order_by('-fecha')

    # Aplicar filtros si vienen
    if fecha_desde:
        try:
            ventas = ventas.filter(fecha__date__gte=fecha_desde)
        except Exception:
            pass
    if fecha_hasta:
        try:
            ventas = ventas.filter(fecha__date__lte=fecha_hasta)
        except Exception:
            pass
    if metodo:
        ventas = ventas.filter(metodo_pago=metodo)
    if usuario:
        try:
            ventas = ventas.filter(usuario__id=int(usuario))
        except Exception:
            pass

    # Limitar resultado razonable
    ventas = ventas[:200]

    # Preparar opciones para selects
    User = get_user_model()
    usuarios = User.objects.order_by('username')
    metodo_choices = MetodoPago.choices

    filtros = {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'metodo': metodo,
        'usuario': usuario,
    }

    return render(request, 'ventas/venta_list.html', {
        'ventas': ventas,
        'usuarios': usuarios,
        'metodo_choices': metodo_choices,
        'filtros': filtros,
    })


@login_required
@role_required(Role.ENCARGADO)
def ventas_reporte_por_dia(request):
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    qs = Venta.objects.select_related('caja')
    if fecha_desde:
        try:
            qs = qs.filter(caja__fecha__gte=fecha_desde)
        except Exception:
            pass
    if fecha_hasta:
        try:
            qs = qs.filter(caja__fecha__lte=fecha_hasta)
        except Exception:
            pass

    rows = (
        qs.values('caja__fecha')
        .annotate(cantidad_ventas=Count('id'), total=Sum('total'))
        .order_by('-caja__fecha')
    )
    total_general = qs.aggregate(total=Sum('total')).get('total') or Decimal('0.00')

    return render(request, 'ventas/reporte_ventas_por_dia.html', {
        'rows': rows,
        'filtros': {'fecha_desde': fecha_desde, 'fecha_hasta': fecha_hasta},
        'total_general': total_general,
    })


@login_required
@role_required(Role.ENCARGADO)
def ventas_reporte_por_metodo(request):
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    qs = Venta.objects.select_related('caja')
    if fecha_desde:
        try:
            qs = qs.filter(caja__fecha__gte=fecha_desde)
        except Exception:
            pass
    if fecha_hasta:
        try:
            qs = qs.filter(caja__fecha__lte=fecha_hasta)
        except Exception:
            pass

    rows = (
        qs.values('metodo_pago')
        .annotate(cantidad_ventas=Count('id'), total=Sum('total'))
        .order_by('-total')
    )
    total_general = qs.aggregate(total=Sum('total')).get('total') or Decimal('0.00')

    # Mapear display del método con choices
    metodo_map = dict(MetodoPago.choices)
    for r in rows:
        r['metodo_display'] = metodo_map.get(r['metodo_pago'], r['metodo_pago'])

    return render(request, 'ventas/reporte_ventas_por_metodo.html', {
        'rows': rows,
        'filtros': {'fecha_desde': fecha_desde, 'fecha_hasta': fecha_hasta},
        'total_general': total_general,
    })


@login_required
@role_required(Role.ENCARGADO)
def venta_detail(request, pk):
    """Muestra detalle de una venta (productos, cantidades, precios, subtotales, total, método, fecha)."""
    venta = get_object_or_404(Venta.objects.select_related('usuario', 'caja').prefetch_related('detalles__producto'), pk=pk)
    return render(request, 'ventas/venta_detail.html', {'venta': venta})


@login_required
@role_required(Role.ENCARGADO)
def venta_comprobante(request, pk):
    """Renderiza un comprobante/boleta imprimible para la venta."""
    venta = get_object_or_404(Venta.objects.select_related('usuario', 'caja').prefetch_related('detalles__producto'), pk=pk)
    # plantilla optimizada para impresión; el usuario puede usar Ctrl+P
    return render(request, 'ventas/venta_comprobante.html', {'venta': venta})


@login_required
@role_required(Role.ENCARGADO)
def venta_exists(request, pk):
    """Endpoint simple que devuelve JSON indicando si la venta existe (no lanza 404).

    Devuelve 200 con {'exists': true/false} para que el cliente verifique sin navegar.
    """
    exists = Venta.objects.filter(pk=pk).exists()
    return JsonResponse({'exists': exists})


@transaction.atomic
@login_required
@role_required(Role.ENCARGADO)
def venta_create(request):
    User = get_user_model()
    
    # Obtener usuario actual y caja activa automáticamente
    usuario_actual = request.user
    caja_activa = Caja.objects.filter(abierta=True).first()
    
    if not caja_activa:
        messages.error(request, 'No hay una caja abierta. Por favor, abra una caja primero.')
        return redirect('home')
    
    metodo_choices = MetodoPago.choices
    unidad_choices = UnidadVenta.choices

    productos = Producto.objects.all()
    products_data = []
    product_stock_map = {}
    
    for p in productos:
        if p.stock_actual_base > 0:
            # compute cantidad depending on unidad_base
            if p.tipo_producto == 'PACK' and p.unidades_por_pack:
                cantidad = float(p.unidades_por_pack)
            elif p.tipo_producto == 'GRANEL' and p.kg_por_caja:
                cantidad = float(p.kg_por_caja)
            else:
                cantidad = 1.0

            products_data.append({
                'id': p.id,
                'codigo_barra': p.codigo_barra,
                'nombre': p.nombre,
                'precio': float(p.precio_venta),
                'precio_venta': float(p.precio_venta),
                'tipo_producto': p.tipo_producto,
                'producto_nombre': p.nombre,
                'cantidad': cantidad,
                'unidad': p.unidad_base
            })
            product_stock_map[str(p.id)] = str(p.stock_actual_base)

    if request.method == 'POST':
        vform = VentaForm(request.POST, metodo_choices=metodo_choices)
        dformset = VentaDetalleFormSet(request.POST, form_kwargs={'unidad_choices': unidad_choices})

        if vform.is_valid() and dformset.is_valid():
            def _to_decimal(val, default=Decimal('0')):
                try:
                    return Decimal(str(val))
                except Exception:
                    return default

            def _compute_cantidad_base(producto, unidad_venta, cantidad_ingresada):
                """Convierte la cantidad ingresada (unidad de venta) a cantidad_base (unidad de stock).

                Regla: stock_actual_base está expresado en la unidad definida por `producto.unidad_base`.
                - UNITARIO: UNIDAD (base = unidades)
                - GRANEL: KG (base = kg)
                - PACK: puede ser PACK (base = cajas) o UNIDAD (base = unidades)
                """
                q = _to_decimal(cantidad_ingresada)

                # Normalizar a 3 decimales para mantener consistencia con los campos DecimalField(..., decimal_places=3)
                def q3(x):
                    try:
                        return x.quantize(Decimal('0.001'))
                    except Exception:
                        return x

                if unidad_venta == 'CAJA':
                    # PACK: si el stock base está en UNIDAD, convertir cajas -> unidades
                    if getattr(producto, 'tipo_producto', None) == 'PACK':
                        unidades_por_pack = getattr(producto, 'unidades_por_pack', None)
                        if getattr(producto, 'unidad_base', None) == 'UNIDAD' and unidades_por_pack:
                            return q3(q * _to_decimal(unidades_por_pack))
                        return q3(q)

                    # GRANEL (fallback): si alguna vez se vende por caja, convertir cajas -> kg
                    if getattr(producto, 'tipo_producto', None) == 'GRANEL':
                        kg_por_caja = getattr(producto, 'kg_por_caja', None)
                        if getattr(producto, 'unidad_base', None) == 'KG' and kg_por_caja:
                            return q3(q * _to_decimal(kg_por_caja))
                        return q3(q)

                    # Otros tipos: por defecto 1 caja = 1 base
                    return q3(q)

                # UNIDAD / KG: ya están en unidad base
                return q3(q)
            # aggregate required stock per producto
            required = {}
            detalles = []
            for form in dformset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    producto = form.cleaned_data['producto']
                    unidad_venta = form.cleaned_data['unidad_venta']
                    cantidad_ingresada = form.cleaned_data['cantidad_ingresada']

                    # Reject non-positive quantities (server-side protection)
                    try:
                        if Decimal(cantidad_ingresada) <= 0:
                            messages.error(request, 'Cantidad inválida en alguno de los productos (debe ser mayor que 0).')
                            return render(request, 'ventas/venta_form.html', {
                                'vform': vform,
                                'dformset': dformset,
                                'products': products_data,
                                'product_stock_map': product_stock_map,
                                'unidad_choices': unidad_choices,
                            })
                    except Exception:
                        messages.error(request, 'Cantidad inválida en alguno de los productos.')
                        return render(request, 'ventas/venta_form.html', {
                            'vform': vform,
                            'dformset': dformset,
                            'products': products_data,
                            'product_stock_map': product_stock_map,
                            'unidad_choices': unidad_choices,
                        })

                    # Convertir a unidad base (para control de stock y reportes)
                    cantidad_base = _compute_cantidad_base(producto, unidad_venta, cantidad_ingresada)

                    # accumulate per producto
                    required.setdefault(producto.id, Decimal('0'))
                    required[producto.id] += cantidad_base

                    # compute precio_unitario
                    precio_unitario = producto.precio_venta

                    # Subtotal debe calcularse en base a la unidad real vendida (cantidad_base)
                    subtotal = (precio_unitario * _to_decimal(cantidad_base)).quantize(Decimal('0.01'))

                    detalles.append({
                        'producto': producto,
                        'unidad_venta': unidad_venta,
                        'cantidad_ingresada': cantidad_ingresada,
                        'cantidad_base': cantidad_base,
                        'precio_unitario': precio_unitario,
                        'subtotal': subtotal
                    })

            # check stock availability
            stock_insuficiente = False
            for producto_id, required_qty in required.items():
                available_stock = product_stock_map.get(str(producto_id), '0')
                if Decimal(required_qty) > Decimal(available_stock):
                    stock_insuficiente = True
                    break

            if stock_insuficiente:
                messages.error(request, 'Stock insuficiente para algunos productos.')
                return render(request, 'ventas/venta_form.html', {
                    'vform': vform,
                    'dformset': dformset,
                    'products': products_data,
                    'product_stock_map': product_stock_map,
                    'unidad_choices': unidad_choices,
                })

            # create venta con usuario y caja automáticos
            venta = Venta.objects.create(
                metodo_pago=vform.cleaned_data['metodo_pago'],
                usuario=usuario_actual,
                caja=caja_activa,
                total=sum(d['subtotal'] for d in detalles)
            )

            # Registrar actividad (defensivo, por si el signal no se ejecuta o se omitió)
            try:
                # Debug: log venta total raw to detect scale issues
                try:
                    print(f"DEBUG_VENTA Venta {venta.id} total (raw): {venta.total}")
                except Exception:
                    print("DEBUG_VENTA Venta unknown total")

                # Format the total for consistent display (thousands separator, no decimals)
                try:
                    venta_total_fmt = format_money(venta.total)
                except Exception:
                    venta_total_fmt = str(venta.total)

                descr = f'Venta {venta.id} total ${venta_total_fmt} ({venta.metodo_pago})'
                if not Actividad.objects.filter(tipo_accion='VENTA', caja=caja_activa, descripcion__icontains=f'Venta {venta.id}').exists():
                    Actividad.objects.create(
                        usuario=usuario_actual,
                        tipo_accion='VENTA',
                        descripcion=descr,
                        caja=caja_activa
                    )
            except Exception:
                # No interrumpir la creación de la venta si falla la auditoría
                pass



            # create venta detalles y actualizar stock
            for detalle_data in detalles:
                VentaDetalle.objects.create(
                    venta=venta,
                    producto=detalle_data['producto'],
                    unidad_venta=detalle_data['unidad_venta'],
                    cantidad_ingresada=detalle_data['cantidad_ingresada'],
                    cantidad_base=detalle_data['cantidad_base'],
                    precio_unitario=detalle_data['precio_unitario'],
                    subtotal=detalle_data['subtotal']
                )
                
                # Descontar stock del producto
                producto = detalle_data['producto']
                producto.stock_actual_base -= detalle_data['cantidad_base']
                producto.save()
                # Si el stock queda por debajo o igual al mínimo, generar actividad de alerta
                try:
                    if producto.stock_minimo is not None and producto.stock_actual_base is not None and producto.stock_actual_base <= producto.stock_minimo:
                        # Evitar duplicados iguales en la misma caja
                        # Usar las propiedades de producto para formatear según tipo (GRANEL vs UNIDAD/PACK)
                        prod_name = str(producto.nombre).lower()
                        try:
                            sd = producto.stock_display
                            if isinstance(sd, str) and ' ' in sd:
                                # e.g. '100.000 kg' -> format numeric part
                                parts = sd.rsplit(' ', 1)
                                sd_num = format_decimal(parts[0])
                                actual_display = f"{sd_num} {parts[1]}"
                            else:
                                actual_display = format_decimal(sd)
                        except Exception:
                            actual_display = format_decimal(producto.stock_actual_base)
                        try:
                            smd = producto.stock_minimo_display
                            if isinstance(smd, str) and ' ' in smd:
                                parts = smd.rsplit(' ', 1)
                                smd_num = format_decimal(parts[0])
                                minimo_display = f"{smd_num} {parts[1]}"
                            else:
                                minimo_display = format_decimal(smd)
                        except Exception:
                            minimo_display = format_decimal(producto.stock_minimo)
                        descr = f'Stock bajo: {prod_name} = {actual_display} (mínimo {minimo_display})'
                        # Only skip if a STOCK_BAJO for this product exists in the same caja within the last hour
                        try:
                            Actividad.objects.create(
                                usuario=usuario_actual,
                                tipo_accion='STOCK_BAJO',
                                descripcion=descr,
                                caja=caja_activa
                            )
                            print(f"DEBUG_ACTIVIDAD: Created STOCK_BAJO for {prod_name} in caja {caja_activa}")
                        except Exception as e:
                            print(f"DEBUG_ACTIVIDAD: Failed to create STOCK_BAJO for {prod_name}: {e}")
                except Exception:
                    pass

            # En lugar de redirigir inmediatamente, mostrar confirmación con opción de imprimir boleta
            return render(request, 'ventas/venta_confirm_print.html', {
                'venta': venta,
            })

    else:
        vform = VentaForm(metodo_choices=metodo_choices)
        dformset = VentaDetalleFormSet(form_kwargs={'unidad_choices': unidad_choices})

    # Serializar a JSON para evitar que Python 'None' aparezca como 'None' en JS
    products_json = mark_safe(json.dumps(products_data))
    stock_map_json = mark_safe(json.dumps(product_stock_map))

    return render(request, 'ventas/venta_form.html', {
        'vform': vform,
        'dformset': dformset,
        'products': products_json,
        'product_stock_map': stock_map_json,
        'unidad_choices': unidad_choices,
        'caja_activa': caja_activa,
        'usuario_actual': usuario_actual,
    })


@login_required
@require_POST
@role_required(Role.ENCARGADO)
def agregar_producto_ajax(request):
    """Endpoint AJAX para buscar un producto por `codigo` (o id) y devolver datos mínimos.
    Espera JSON: {"codigo": "...", "cantidad": 1}
    """
    try:
        payload = json.loads(request.body)
    except Exception:
        payload = request.POST

    codigo = payload.get('codigo')
    cantidad = payload.get('cantidad', 1)

    if not codigo:
        return JsonResponse({'ok': False, 'error': 'Código vacío'}, status=400)

    # Buscar por código de barra o por id
    producto = None
    try:
        producto = Producto.objects.get(codigo_barra=codigo)
    except Exception:
        try:
            producto = Producto.objects.get(pk=int(codigo))
        except Exception:
            return JsonResponse({'ok': False, 'error': 'Producto no encontrado'}, status=404)

    # Verificar stock si aplica
    try:
        q = Decimal(str(cantidad))
    except Exception:
        q = Decimal('1')

    if producto.stock_actual_base is not None and q > producto.stock_actual_base:
        return JsonResponse({'ok': False, 'error': 'Stock insuficiente', 'available': str(producto.stock_actual_base)}, status=400)

    # Responder con datos para que el frontend agregue la línea
    data = {
        'ok': True,
        'producto': {
            'id': producto.id,
            'codigo_barra': producto.codigo_barra,
            'nombre': producto.nombre,
            'precio_venta': float(producto.precio_venta),
            'tipo_producto': producto.tipo_producto,
            'unidad_base': producto.unidad_base,
            'stock_actual_base': float(producto.stock_actual_base or 0),
        }
    }
    return JsonResponse(data)