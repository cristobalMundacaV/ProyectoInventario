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

                    # compute cantidad_base
                    if unidad_venta == 'UNIDAD' or unidad_venta == 'KG':
                        cantidad_base = cantidad_ingresada
                    elif unidad_venta == 'CAJA':
                        if producto.unidades_por_pack:
                            cantidad_base = cantidad_ingresada * Decimal(producto.unidades_por_pack)
                        elif producto.kg_por_caja:
                            cantidad_base = cantidad_ingresada * Decimal(producto.kg_por_caja)
                        else:
                            cantidad_base = cantidad_ingresada
                    else:
                        cantidad_base = cantidad_ingresada

                    # accumulate per product
                    required.setdefault(producto.id, Decimal('0'))
                    required[producto.id] += cantidad_base

                    # compute precio_unitario
                    if unidad_venta == 'CAJA' and producto.unidades_por_pack:
                        precio_unitario = producto.precio_venta * Decimal(producto.unidades_por_pack)
                    else:
                        precio_unitario = producto.precio_venta

                    subtotal = (precio_unitario * cantidad_ingresada).quantize(Decimal('0.01'))

                    detalles.append({
                        'producto': producto,
                        'unidad_venta': unidad_venta,
                        'cantidad_ingresada': cantidad_ingresada,
                        'cantidad_base': cantidad_base,
                        'precio_unitario': precio_unitario,
                        'subtotal': subtotal,
                    })

            # validate stock
            insuficiente = []
            for pid, req in required.items():
                prod = Producto.objects.get(id=pid)
                if req > prod.stock_base:
                    insuficiente.append((prod, req, prod.stock_base))

            if insuficiente:
                for prod, req, avail in insuficiente:
                    messages.error(request, f'Stock insuficiente para {prod.nombre}: requerido {req}, disponible {avail}')
            else:
                # save venta and detalles
                venta = Venta.objects.create(
                    metodo_pago=vform.cleaned_data['metodo_pago'],
                    usuario=vform.cleaned_data['usuario'],
                    caja=vform.cleaned_data['caja'],
                    total=Decimal('0.00')
                )
                total = Decimal('0.00')
                for det in detalles:
                    VentaDetalle.objects.create(
                        venta=venta,
                        producto=det['producto'],
                        cantidad_ingresada=det['cantidad_ingresada'],
                        unidad_venta=det['unidad_venta'],
                        cantidad_base=det['cantidad_base'],
                        precio_unitario=det['precio_unitario'],
                        subtotal=det['subtotal'],
                    )
                    # descontar stock
                    p = det['producto']
                    p.stock_base = p.stock_base - det['cantidad_base']
                    p.save()
                    total += det['subtotal']

                venta.total = total.quantize(Decimal('0.01'))
                venta.save()

                messages.success(request, 'Venta registrada y stock descontado correctamente.')
                return redirect('venta_list')
        else:
            messages.error(request, 'Corrige los errores en el formulario.')
    else:
        vform = VentaForm(metodo_choices=metodo_choices, usuario_qs=usuarios, caja_qs=cajas)
        dformset = VentaDetalleFormSet(form_kwargs={'unidad_choices': unidad_choices})

    context = {
        'vform': vform,
        'dformset': dformset,
        'product_stock_map': product_stock_map,
        'products': products,
        'unidad_choices': unidad_choices,
    }
    return render(request, 'ventas/venta_form.html', context)
