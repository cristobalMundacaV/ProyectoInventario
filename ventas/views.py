from decimal import Decimal
from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib import messages

from core.enums import MetodoPago, UnidadVenta
from usuarios.models import Usuario
from caja.models import Caja
from inventario.models import Producto
from .models import Venta, VentaDetalle
from .forms import VentaForm, VentaDetalleFormSet


def venta_list(request):
    ventas = Venta.objects.order_by('-fecha')[:50]
    return render(request, 'ventas/venta_list.html', {'ventas': ventas})


@transaction.atomic
def venta_create(request):
    metodo_choices = MetodoPago.choices
    unidad_choices = UnidadVenta.choices
    usuarios = Usuario.objects.filter(activo=True)
    cajas = Caja.objects.all()

    products = Producto.objects.filter(activo=True)
    product_stock_map = {str(p.id): str(p.stock_display) for p in products}

    if request.method == 'POST':
        vform = VentaForm(request.POST, metodo_choices=metodo_choices, usuario_qs=usuarios, caja_qs=cajas)
        dformset = VentaDetalleFormSet(request.POST, form_kwargs={'unidad_choices': unidad_choices})

        if vform.is_valid() and dformset.is_valid():
            # aggregate required stock per product
            required = {}
            detalles = []
            for form in dformset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    producto = form.cleaned_data['producto']
                    unidad_venta = form.cleaned_data['unidad_venta']
                    cantidad_ingresada = form.cleaned_data['cantidad_ingresada']

                    # compute cantidad_base (simplificado)
                    cantidad_base = cantidad_ingresada

                    # accumulate per product
                    required.setdefault(producto.id, Decimal('0'))
                    required[producto.id] += cantidad_base

                    # compute precio_unitario (simplificado)
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
            for product_id, required_qty in required.items():
                available_stock = product_stock_map.get(str(product_id), '0')
                if Decimal(required_qty) > Decimal(available_stock):
                    stock_insuficiente = True
                    break

            if stock_insuficiente:
                messages.error(request, 'Stock insuficiente para algunos productos.')
                return render(request, 'ventas/venta_form.html', {
                    'vform': vform,
                    'dformset': dformset,
                    'products': products,
                    'product_stock_map': product_stock_map,
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
                    producto=detalle_data['producto'],
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
        'products': products,
        'product_stock_map': product_stock_map,
        'unidad_choices': unidad_choices,
    })