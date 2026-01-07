from decimal import Decimal
from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import get_user_model

from core.enums import MetodoPago, UnidadVenta
from caja.models import Caja
from inventario.models import Producto
from .models import Venta, VentaDetalle
from .forms import VentaForm, VentaDetalleFormSet


def venta_list(request):
    ventas = Venta.objects.order_by('-fecha')[:50]
    return render(request, 'ventas/venta_list.html', {'ventas': ventas})


@transaction.atomic
def venta_create(request):
    User = get_user_model()
    
    # Obtener usuario actual y caja activa automáticamente
    usuario_actual = request.user
    caja_activa = Caja.objects.filter(abierta=True).first()
    
    if not caja_activa:
        messages.error(request, 'No hay una caja abierta. Por favor, abra una caja primero.')
        return redirect('caja_list')
    
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
                'producto_nombre': p.nombre,
                'cantidad': cantidad,
                'unidad': p.unidad_base
            })
            product_stock_map[str(p.id)] = str(p.stock_actual_base)

    if request.method == 'POST':
        vform = VentaForm(request.POST, metodo_choices=metodo_choices)
        dformset = VentaDetalleFormSet(request.POST, form_kwargs={'unidad_choices': unidad_choices})

        if vform.is_valid() and dformset.is_valid():
            # aggregate required stock per producto
            required = {}
            detalles = []
            for form in dformset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    producto = form.cleaned_data['producto']
                    unidad_venta = form.cleaned_data['unidad_venta']
                    cantidad_ingresada = form.cleaned_data['cantidad_ingresada']

                    # compute cantidad_base (simplificado)
                    cantidad_base = cantidad_ingresada

                    # accumulate per producto
                    required.setdefault(producto.id, Decimal('0'))
                    required[producto.id] += cantidad_base

                    # compute precio_unitario
                    precio_unitario = producto.precio_venta

                    subtotal = (precio_unitario * cantidad_ingresada).quantize(Decimal('0.01'))

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

            messages.success(request, 'Venta creada exitosamente.')
            return redirect('venta_list')

    else:
        vform = VentaForm(metodo_choices=metodo_choices)
        dformset = VentaDetalleFormSet(form_kwargs={'unidad_choices': unidad_choices})

    return render(request, 'ventas/venta_form.html', {
        'vform': vform,
        'dformset': dformset,
        'products': products_data,
        'product_stock_map': product_stock_map,
        'unidad_choices': unidad_choices,
        'caja_activa': caja_activa,
        'usuario_actual': usuario_actual,
    })