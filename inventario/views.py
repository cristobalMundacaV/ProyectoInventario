from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models.deletion import ProtectedError
from django.contrib import messages
from django.db import transaction
from django.forms import inlineformset_factory

from .models import Producto, Categoria, IngresoStock, IngresoStockDetalle
from .forms import ProductoForm, AnadirStockForm, IngresoStockForm, IngresoStockDetalleForm
from inventario.templatetags.format_numbers import format_decimal
from auditoria.models import Actividad
from caja.models import Caja
from decimal import Decimal
from django.db.models import F, Sum, Q
from django.core.exceptions import ValidationError

from core.authz import role_required, admin_required
from core.roles import Role
from core.roles import is_admin


# --- Vista para añadir stock ---
@login_required
@role_required(Role.ENCARGADO)
def anadir_stock(request):
    if request.method == 'POST':
        form = AnadirStockForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            cantidad = form.cleaned_data['cantidad']
            producto.stock_actual_base = (producto.stock_actual_base or 0) + cantidad
            producto.save()
            # Formatear cantidades para mostrar sin ceros innecesarios
            if producto.tipo_producto == 'GRANEL':
                unidad_label = 'kg'
                stock_unit_label = 'kg'
            else:
                unidad_label = 'unidad' if cantidad == Decimal('1') else 'unidades'
                # Para el stock actual, decidir plural según el valor actual del stock
                stock_unit_label = 'unidad' if (producto.stock_actual_base == Decimal('1')) else 'unidades'
            cantidad_display = format_decimal(cantidad)
            stock_display = format_decimal(producto.stock_actual_base)
            messages.success(request, f'Se añadió {cantidad_display} {unidad_label} al stock de {producto.nombre}. Stock actual: {stock_display} {stock_unit_label}')
            # Registrar actividad de ingreso de stock con unidad adecuada
            if producto.tipo_producto == 'GRANEL':
                unidad_label = 'kg'
            else:
                unidad_label = 'unidad' if cantidad == Decimal('1') else 'unidades'
            Actividad.objects.create(
                usuario=request.user,
                tipo_accion='INGRESO_STOCK',
                descripcion=f'Se añadió {cantidad_display} {unidad_label} al stock de {producto.nombre}',
                caja=(Caja.objects.filter(abierta=True).order_by('-hora_apertura').first())
            )
            if 'add_another' in request.POST:
                return redirect('anadir_stock')
            return redirect('producto_list')
    else:
        form = AnadirStockForm()
    # If reached here due to invalid POST, or GET, decide rendering
    if request.method == 'POST' and not form.is_valid():
        # Re-render the producto list with the form errors inside the modal
        nombre = request.GET.get('nombre', '')
        categoria = request.GET.get('categoria', '')
        codigo_barra = request.GET.get('codigo_barra', '')

        productos = Producto.objects.all()
        if nombre:
            productos = productos.filter(nombre__icontains=nombre)
        if categoria:
            productos = productos.filter(categoria_id=categoria)
        if codigo_barra:
            productos = productos.filter(codigo_barra__icontains=codigo_barra)

        categorias = Categoria.objects.all()
        categoria_form = CategoriaForm()
        return render(request, 'inventario/producto_list.html', {
            'productos': productos,
            'categorias': categorias,
            'filtros': {
                'nombre': nombre,
                'categoria': categoria,
                'codigo_barra': codigo_barra,
            },
            'categoria_form': categoria_form,
            'anadir_stock_form': form,
            'open_modal': 'anadir_stock',
        })

    return render(request, 'inventario/anadir_stock_form.html', {'form': form})


# --- Vista para crear categoría ---
from django import forms
 


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        qs = Categoria.objects.filter(nombre__iexact=nombre)
        if self.instance and getattr(self.instance, 'pk', None):
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Ya existe una categoría con ese nombre.')
        return nombre


@login_required
@role_required(Role.ENCARGADO)
def categoria_create(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, 'Categoría creada correctamente.')
            return redirect('producto_list')
    else:
        form = CategoriaForm()

    if request.method == 'POST' and not form.is_valid():
        # Re-render producto list with category form errors and open modal
        nombre = request.GET.get('nombre', '')
        categoria = request.GET.get('categoria', '')
        codigo_barra = request.GET.get('codigo_barra', '')

        productos = Producto.objects.all()
        if nombre:
            productos = productos.filter(nombre__icontains=nombre)
        if categoria:
            productos = productos.filter(categoria_id=categoria)
        if codigo_barra:
            productos = productos.filter(codigo_barra__icontains=codigo_barra)

        categorias = Categoria.objects.all()
        anadir_stock_form = AnadirStockForm()
        return render(request, 'inventario/producto_list.html', {
            'productos': productos,
            'categorias': categorias,
            'filtros': {
                'nombre': nombre,
                'categoria': categoria,
                'codigo_barra': codigo_barra,
            },
            'categoria_form': form,
            'anadir_stock_form': anadir_stock_form,
            'open_modal': 'categoria',
        })

    return render(request, 'inventario/categoria_form.html', {'form': form})


@login_required
@role_required(Role.ENCARGADO)
def categoria_list(request):
    categorias = Categoria.objects.all().order_by('nombre')
    # incluir conteo de productos por categoría en la plantilla
    return render(request, 'inventario/categoria_list.html', {
        'categorias': categorias,
    })


@login_required
@role_required(Role.ENCARGADO)
def categoria_update(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, 'Categoría actualizada correctamente.')
            return redirect('categoria_list')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'inventario/categoria_form.html', {'form': form})


@login_required
@admin_required
def categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        try:
            nombre = categoria.nombre
            categoria.delete()
            messages.success(request, 'Categoría eliminada correctamente.')
            return redirect('categoria_list')
        except ProtectedError:
            messages.error(request, 'No se puede eliminar la categoría porque tiene productos asociados.')
            return redirect('categoria_list')
    # Si la categoría tiene productos asociados, marcar como protegida y pasar los relacionados
    protected = categoria.productos.exists()
    related_products = categoria.productos.all() if protected else None
    return render(request, 'inventario/categoria_confirm_delete.html', {
        'categoria': categoria,
        'protected': protected,
        'related_products': related_products,
    })

@login_required
@role_required(Role.ENCARGADO)
def productos_vendidos(request):
    """Lista de productos ordenada por unidades vendidas (mayor a menor).
    Opcional: filtrar por rango de fechas con GET `start` y `end` (YYYY-MM-DD).
    """
    start = request.GET.get('start')
    end = request.GET.get('end')

    if start and end:
        fecha_filter = Q(ventadetalle__venta__fecha__range=(start, end))
        productos = Producto.objects.annotate(
            total_vendido=Sum('ventadetalle__cantidad_base', filter=fecha_filter)
        ).order_by('-total_vendido')
    else:
        productos = Producto.objects.annotate(
            total_vendido=Sum('ventadetalle__cantidad_base')
        ).order_by('-total_vendido')

    categorias = Categoria.objects.all()
    return render(request, 'inventario/producto_vendidos.html', {
        'productos': productos,
        'categorias': categorias,
        'filtros': {'start': start, 'end': end},
    })


@login_required
@role_required(Role.ENCARGADO)
def producto_list(request):
    nombre = request.GET.get('nombre', '')
    categoria = request.GET.get('categoria', '')
    codigo_barra = request.GET.get('codigo_barra', '')
    bajo_stock_flag = request.GET.get('bajo_stock')

    productos = Producto.objects.all()
    if nombre:
        productos = productos.filter(nombre__icontains=nombre)
    if categoria:
        productos = productos.filter(categoria_id=categoria)
    if codigo_barra:
        productos = productos.filter(codigo_barra__icontains=codigo_barra)

    # Si se pidió filtrar por bajo stock, limitar el queryset
    if bajo_stock_flag:
        # Considerar sólo productos con stock_minimo > 0 y stock_actual_base <= stock_minimo
        productos = productos.filter(stock_minimo__gt=0).filter(stock_actual_base__lte=F('stock_minimo'))

    categorias = Categoria.objects.all()
    # Mark products that are at or below minimum stock for the template
    for p in productos:
        try:
            p.bajo_stock = (p.stock_actual_base is not None and p.stock_minimo is not None and p.stock_actual_base <= p.stock_minimo)
        except Exception:
            p.bajo_stock = False
    # Instanciar formularios para mostrarlos en la vista de lista (modales)
    categoria_form = CategoriaForm()
    anadir_stock_form = AnadirStockForm()

    return render(request, 'inventario/producto_list.html', {
        'productos': productos,
        'categorias': categorias,
        'filtros': {
            'nombre': nombre,
            'categoria': categoria,
            'codigo_barra': codigo_barra,
            'bajo_stock': bool(bajo_stock_flag),
        },
        'categoria_form': categoria_form,
        'anadir_stock_form': anadir_stock_form,
    })


@login_required
@role_required(Role.ENCARGADO)
def ingreso_stock_list(request):
    ingresos = IngresoStock.objects.select_related('usuario').prefetch_related('detalles').order_by('-fecha')
    return render(request, 'inventario/ingreso_stock_list.html', {
        'ingresos': ingresos,
    })


@login_required
@role_required(Role.ENCARGADO)
def ingreso_stock_detail(request, pk):
    ingreso = get_object_or_404(
        IngresoStock.objects.select_related('usuario').prefetch_related('detalles__producto'),
        pk=pk,
    )
    return render(request, 'inventario/ingreso_stock_detail.html', {
        'ingreso': ingreso,
    })


@login_required
@role_required(Role.ENCARGADO)
def ingreso_stock_create(request):
    DetalleFormSet = inlineformset_factory(
        IngresoStock,
        IngresoStockDetalle,
        form=IngresoStockDetalleForm,
        extra=5,
        can_delete=True,
    )

    if request.method == 'POST':
        form = IngresoStockForm(request.POST)
        formset = DetalleFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                ingreso = form.save(commit=False)
                ingreso.usuario = request.user
                ingreso.save()

                formset.instance = ingreso
                detalles = formset.save(commit=False)

                # Build a human-friendly summary for the audit entry.
                # We aggregate quantities per product so the activity reads like:
                # "Ingreso de stock (FACTURA 123) items: Coca Cola +2 unid, Harina +1 kg"
                items_por_producto = {}
                for det in detalles:
                    if det.producto_id is None or det.cantidad_base is None:
                        continue
                    if det.cantidad_base <= 0:
                        continue

                    Producto.objects.filter(pk=det.producto_id).update(
                        stock_actual_base=F('stock_actual_base') + det.cantidad_base
                    )
                    det.ingreso = ingreso
                    det.save()
                    try:
                        prod = det.producto
                        key = (prod.pk, prod.nombre, prod.tipo_producto)
                        items_por_producto[key] = (items_por_producto.get(key) or Decimal('0')) + det.cantidad_base
                    except Exception:
                        # Best-effort: if anything goes wrong building the summary, still record the ingreso.
                        pass

                for obj in formset.deleted_objects:
                    obj.delete()

                caja_abierta = Caja.objects.filter(abierta=True).order_by('-hora_apertura').first()
                doc = ingreso.tipo_documento
                if ingreso.numero_documento:
                    doc = f"{doc} {ingreso.numero_documento}"

                partes_items = []
                try:
                    for (_, nombre, tipo_prod), cantidad_total in items_por_producto.items():
                        if tipo_prod == 'GRANEL':
                            unidad = 'kg'
                        else:
                            unidad = 'unidad' if cantidad_total == Decimal('1') else 'unidades'
                        partes_items.append(f"{nombre} +{format_decimal(cantidad_total)} {unidad}")
                except Exception:
                    partes_items = []

                if partes_items:
                    items_txt = ", ".join(partes_items)
                    descripcion = f"Ingreso de stock ({doc}) items: {items_txt}"
                else:
                    # Fallback if we couldn't build a per-item summary.
                    descripcion = f"Ingreso de stock ({doc})"

                Actividad.objects.create(
                    usuario=request.user,
                    tipo_accion='INGRESO_STOCK',
                    descripcion=descripcion,
                    caja=caja_abierta,
                )

            messages.success(request, 'Ingreso de stock registrado correctamente.')
            return redirect('ingreso_stock_detail', pk=ingreso.pk)
        messages.error(request, 'No se pudo registrar el ingreso. Revise los datos.')
    else:
        form = IngresoStockForm()
        formset = DetalleFormSet()

    return render(request, 'inventario/ingreso_stock_form.html', {
        'form': form,
        'formset': formset,
    })


@login_required
@role_required(Role.ENCARGADO)
def productos_bajo_stock(request):
    productos = Producto.objects.filter(stock_minimo__gt=0).filter(stock_actual_base__lte=F('stock_minimo')).order_by('nombre')
    for p in productos:
        p.bajo_stock = True
    return render(request, 'inventario/productos_bajo_stock.html', {
        'productos': productos,
    })

@login_required
@admin_required
def producto_create(request):
    if request.method == 'POST':
        producto_form = ProductoForm(request.POST, user=request.user)

        if producto_form.is_valid():
            try:
                producto = producto_form.save()
                return redirect('producto_list')
            except Exception as e:
                # Mostrar error al usuario con detalles mínimos para depuración
                messages.error(request, f'Error al guardar el producto: {str(e)}')
        else:
            # Mostrar errores de validación en un mensaje para facilitar depuración en UI
            try:
                errores = producto_form.errors.as_text()
            except Exception:
                errores = str(producto_form.errors)
            messages.error(request, 'No se pudo guardar el producto. Errores: ' + errores)
    else:
        producto_form = ProductoForm(user=request.user)

    # Ensure stock fields use integer step and integer initial values when tipo != GRANEL
    tipo = None
    if producto_form.instance and getattr(producto_form.instance, 'tipo_producto', None):
        tipo = producto_form.instance.tipo_producto
    elif producto_form.is_bound:
        tipo = producto_form.data.get('tipo_producto')

    if tipo != 'GRANEL':
        for fname in ('stock_minimo', 'stock_actual_base'):
            if fname in producto_form.fields:
                producto_form.fields[fname].widget.attrs.update({'step': '1'})
                if not producto_form.is_bound:
                    val = getattr(producto_form.instance, fname, None)
                    if val is not None:
                        try:
                            producto_form.initial[fname] = int(val)
                        except Exception:
                            producto_form.initial[fname] = val
    else:
        # Show decimals for stock fields
        for fname in ('stock_minimo', 'stock_actual_base'):
            if fname in producto_form.fields:
                producto_form.fields[fname].widget.attrs.update({'step': '0.01'})
                if not producto_form.is_bound:
                    val = getattr(producto_form.instance, fname, None)
                    if val is not None:
                        try:
                            producto_form.initial[fname] = f"{float(val):.2f}"
                        except Exception:
                            producto_form.initial[fname] = val

    # Ensure precio_compra and precio_venta display as integers
    # Ensure precio_compra and precio_venta display with correct step/format
    for pname in ('precio_compra', 'precio_venta'):
        if pname in producto_form.fields:
            if tipo == 'GRANEL':
                producto_form.fields[pname].widget.attrs.update({'step': '0.01'})
                if not producto_form.is_bound:
                    val = getattr(producto_form.instance, pname, None)
                    if val is not None:
                        try:
                            producto_form.initial[pname] = f"{float(val):.2f}"
                        except Exception:
                            producto_form.initial[pname] = val
            else:
                producto_form.fields[pname].widget.attrs.update({'step': '1'})
                if not producto_form.is_bound:
                    val = getattr(producto_form.instance, pname, None)
                    if val is not None:
                        try:
                            producto_form.initial[pname] = int(val)
                        except Exception:
                            producto_form.initial[pname] = val

    return render(request, 'inventario/producto_form.html', {
        'form': producto_form,
        'accion': 'Nuevo',
        'can_edit_prices': True,
    })


@login_required
@role_required(Role.ENCARGADO)
def producto_update(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    can_edit_prices = is_admin(request.user)
    if request.method == 'POST':
        old_precio_compra = getattr(producto, 'precio_compra', None)
        old_precio_venta = getattr(producto, 'precio_venta', None)
        form = ProductoForm(request.POST, instance=producto, user=request.user)
        if form.is_valid():
            try:
                # Regla: solo Administrador puede cambiar precios
                if not can_edit_prices and ('precio_compra' in form.cleaned_data or 'precio_venta' in form.cleaned_data):
                    new_precio_compra = form.cleaned_data.get('precio_compra')
                    new_precio_venta = form.cleaned_data.get('precio_venta')
                    if (new_precio_compra != old_precio_compra) or (new_precio_venta != old_precio_venta):
                        messages.error(request, 'No tiene permisos para cambiar precios. (Solo Administrador)')
                        return render(request, 'inventario/producto_form.html', {
                            'form': form,
                            'accion': 'Editar',
                            'can_edit_prices': can_edit_prices,
                        })

                producto = form.save(commit=False)
                if producto.tipo_producto in ['PACK', 'UNITARIO']:
                    producto.stock_minimo = int(producto.stock_minimo)
                producto.save()
                return redirect('producto_list')
            except Exception as e:
                messages.error(request, f'Error al actualizar el producto: {str(e)}')
        else:
            try:
                errores = form.errors.as_text()
            except Exception:
                errores = str(form.errors)
            messages.error(request, 'No se pudo actualizar el producto. Errores: ' + errores)
    else:
        form = ProductoForm(instance=producto, user=request.user)
    # Ensure stock fields use integer step and show integer values when product is not GRANEL.
    tipo = None
    if form.instance and getattr(form.instance, 'tipo_producto', None):
        tipo = form.instance.tipo_producto
    elif form.is_bound:
        tipo = form.data.get('tipo_producto')

    if tipo != 'GRANEL':
        for fname in ('stock_minimo', 'stock_actual_base'):
            if fname in form.fields:
                form.fields[fname].widget.attrs.update({'step': '1'})
                # For unbound forms, set initial to integer value from instance
                if not form.is_bound:
                    val = getattr(form.instance, fname, None)
                    if val is not None:
                        try:
                            form.initial[fname] = int(val)
                        except Exception:
                            form.initial[fname] = val
    else:
        # Show decimals for stock fields when GRANEL
        for fname in ('stock_minimo', 'stock_actual_base'):
            if fname in form.fields:
                form.fields[fname].widget.attrs.update({'step': '0.01'})
                if not form.is_bound:
                    val = getattr(form.instance, fname, None)
                    if val is not None:
                        try:
                            form.initial[fname] = f"{float(val):.2f}"
                        except Exception:
                            form.initial[fname] = val

    # Ensure precio_compra and precio_venta display as integers
    # Ensure precio_compra and precio_venta display with correct step/format
    for pname in ('precio_compra', 'precio_venta'):
        if pname in form.fields:
            if tipo == 'GRANEL':
                form.fields[pname].widget.attrs.update({'step': '0.01'})
                if not form.is_bound:
                    val = getattr(form.instance, pname, None)
                    if val is not None:
                        try:
                            form.initial[pname] = f"{float(val):.2f}"
                        except Exception:
                            form.initial[pname] = val
            else:
                form.fields[pname].widget.attrs.update({'step': '1'})
                if not form.is_bound:
                    val = getattr(form.instance, pname, None)
                    if val is not None:
                        try:
                            form.initial[pname] = int(val)
                        except Exception:
                            form.initial[pname] = val

    return render(request, 'inventario/producto_form.html', {
        'form': form,
        'accion': 'Editar',
        'can_edit_prices': can_edit_prices,
    })

@login_required
@admin_required
def producto_delete(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        try:
            producto.delete()
            return redirect('producto_list')
        except ProtectedError:
            # Fetch related VentaDetalle objects to show why deletion failed
            related_detalles = producto.ventadetalle_set.select_related('venta').all()
            return render(request, 'inventario/producto_confirm_delete.html', {
                'producto': producto,
                'protected': True,
                'related_detalles': related_detalles
            })
    return render(request, 'inventario/producto_confirm_delete.html', {'producto': producto})


@login_required
@role_required(Role.ENCARGADO)
def producto_deactivate(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.activo = False
        producto.save()
        # Registrar actividad de desactivación
        Actividad.objects.create(
            usuario=request.user,
            tipo_accion='DESACTIVACION_PRODUCTO',
            descripcion=f'Producto desactivado: {producto.nombre}',
            caja=(Caja.objects.filter(abierta=True).order_by('-hora_apertura').first())
        )
        messages.success(request, 'Producto desactivado correctamente.')
        return redirect('producto_list')


@login_required
@admin_required
def producto_unlink(request, pk):
    """Unlink product from all VentaDetalle (set producto=NULL) but keep the product in the database."""
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        # Bulk update related VentaDetalle to set producto to NULL
        producto.ventadetalle_set.update(producto=None)
        # Registrar actividad de desvinculación
        Actividad.objects.create(
            usuario=request.user,
            tipo_accion='DESVINCULAR_PRODUCTO',
            descripcion=f'Producto desvinculado de ventas: {producto.nombre}',
            caja=(Caja.objects.filter(abierta=True).order_by('-hora_apertura').first())
        )
        messages.success(request, 'Ventas desvinculadas correctamente. El producto se mantiene en el sistema.')
        return redirect('producto_list')
    return redirect('producto_list')
