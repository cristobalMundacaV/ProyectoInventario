from decimal import Decimal
from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import get_user_model

from core.enums import MetodoPago, UnidadVenta
from caja.models import Caja
from inventario.models import Presentacion
from .models import Venta, VentaDetalle
from .forms import VentaForm, VentaDetalleFormSet


def venta_list(request):
    ventas = Venta.objects.order_by('-fecha')[:50]
    return render(request, 'ventas/venta_list.html', {'ventas': ventas})


@transaction.atomic
def venta_create(request):
    User = get_user_model()
    
    metodo_choices = MetodoPago.choices
    unidad_choices = UnidadVenta.choices
    usuarios = User.objects.all()
    cajas = Caja.objects.all()

    presentaciones = Presentacion.objects.all()
    presentaciones_data = []
    presentacion_stock_map = {}
    
    for p in presentaciones:
        if p.stock_base > 0:  # Solo presentaciones con stock
            presentaciones_data.append({
                'id': p.id,
                'codigo_barra': p.codigo_barra,
                'nombre': f"{p.producto.nombre} - {p.nombre}",
                'precio': float(p.precio_venta),
                'producto_nombre': p.producto.nombre,
                'cantidad': float(p.cantidad_base),
                'unidad': p.unidad_venta
            })
            presentacion_stock_map[str(p.id)] = str(p.stock_base)

    if request.method == 'POST':
        vform = VentaForm(request.POST, metodo_choices=metodo_choices, usuario_qs=usuarios, caja_qs=cajas)
        dformset = VentaDetalleFormSet(request.POST, form_kwargs={'unidad_choices': unidad_choices})

        if vform.is_valid() and dformset.is_valid():
            # aggregate required stock per presentacion
            required = {}
            detalles = []
            for form in dformset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    presentacion = form.cleaned_data['presentacion']
                    unidad_venta = form.cleaned_data['unidad_venta']
                    cantidad_ingresada = form.cleaned_data['cantidad_ingresada']

                    # compute cantidad_base (simplificado)
                    cantidad_base = cantidad_ingresada

                    # accumulate per presentacion
                    required.setdefault(presentacion.id, Decimal('0'))
                    required[presentacion.id] += cantidad_base

                    # compute precio_unitario
                    precio_unitario = presentacion.precio_venta

                    subtotal = (precio_unitario * cantidad_ingresada).quantize(Decimal('0.01'))

                    detalles.append({
                        'presentacion': presentacion,
                        'unidad_venta': unidad_venta,
                        'cantidad_ingresada': cantidad_ingresada,
                        'cantidad_base': cantidad_base,
                        'precio_unitario': precio_unitario,
                        'subtotal': subtotal
                    })

            # check stock availability
            stock_insuficiente = False
            for presentacion_id, required_qty in required.items():
                available_stock = presentacion_stock_map.get(str(presentacion_id), '0')
                if Decimal(required_qty) > Decimal(available_stock):
                    stock_insuficiente = True
                    break

            if stock_insuficiente:
                messages.error(request, 'Stock insuficiente para algunas presentaciones.')
                return render(request, 'ventas/venta_form.html', {
                    'vform': vform,
                    'dformset': dformset,
                    'products': presentaciones_data,
                    'product_stock_map': presentacion_stock_map,
                    'unidad_choices': unidad_choices,
                })

            # create venta
            venta = vform.save(commit=False)
            venta.total = sum(d['subtotal'] for d in detalles)
            venta.save()

            # create venta detalles
            for detalle_data in detalles:
                VentaDetalle.objects.create(
                    venta=venta,
                    presentacion=detalle_data['presentacion'],
                    unidad_venta=detalle_data['unidad_venta'],
                    cantidad_ingresada=detalle_data['cantidad_ingresada'],
                    cantidad_base=detalle_data['cantidad_base'],
                    precio_unitario=detalle_data['precio_unitario'],
                    subtotal=detalle_data['subtotal']
                )

            messages.success(request, 'Venta creada exitosamente.')
            return redirect('venta_list')

    else:
        vform = VentaForm(metodo_choices=metodo_choices, usuario_qs=usuarios, caja_qs=cajas)
        dformset = VentaDetalleFormSet(form_kwargs={'unidad_choices': unidad_choices})

    return render(request, 'ventas/venta_form.html', {
        'vform': vform,
        'dformset': dformset,
        'products': presentaciones_data,
        'product_stock_map': presentacion_stock_map,
        'unidad_choices': unidad_choices,
    })