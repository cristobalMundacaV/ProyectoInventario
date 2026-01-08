from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models.deletion import ProtectedError
from django.contrib import messages
from .models import Producto, Categoria
from .forms import ProductoForm, AnadirStockForm
from auditoria.models import Actividad
from caja.models import Caja


# --- Vista para añadir stock ---
@login_required
def anadir_stock(request):
    if request.method == 'POST':
        form = AnadirStockForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            cantidad = form.cleaned_data['cantidad']
            producto.stock_actual_base = (producto.stock_actual_base or 0) + cantidad
            producto.save()
            messages.success(request, f'Se añadió {cantidad} al stock de {producto.nombre}. Stock actual: {producto.stock_actual_base} {"kg" if producto.tipo_producto == "GRANEL" else "unidades"}')
            if 'add_another' in request.POST:
                return redirect('anadir_stock')
            return redirect('producto_list')
    else:
        form = AnadirStockForm()
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


@login_required
def categoria_create(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada correctamente.')
            return redirect('producto_list')
    else:
        form = CategoriaForm()
    return render(request, 'inventario/categoria_form.html', {'form': form})

@login_required
def producto_list(request):
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
    return render(request, 'inventario/producto_list.html', {
        'productos': productos,
        'categorias': categorias,
        'filtros': {
            'nombre': nombre,
            'categoria': categoria,
            'codigo_barra': codigo_barra,
        }
    })

@login_required
def producto_create(request):
    if request.method == 'POST':
        producto_form = ProductoForm(request.POST)

        if producto_form.is_valid():
            producto = producto_form.save()
            # Registrar actividad de creación de producto
            Actividad.objects.create(
                usuario=request.user,
                tipo_accion='CREACION_PRODUCTO',
                descripcion=f'Producto creado: {producto.nombre}',
                caja=(Caja.objects.filter(abierta=True).order_by('-hora_apertura').first())
            )
            return redirect('producto_list')
    else:
        producto_form = ProductoForm()

    return render(request, 'inventario/producto_form.html', {
        'form': producto_form,
        'accion': 'Nuevo'
    })


@login_required
def producto_update(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            producto = form.save(commit=False)
            if producto.tipo_producto in ['PACK', 'UNITARIO']:
                producto.stock_minimo = int(producto.stock_minimo)
            producto.save()
            # Registrar actividad de edición de producto
            Actividad.objects.create(
                usuario=request.user,
                tipo_accion='EDICION_PRODUCTO',
                descripcion=f'Producto editado: {producto.nombre}',
                caja=(Caja.objects.filter(abierta=True).order_by('-hora_apertura').first())
            )
            return redirect('producto_list')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'inventario/producto_form.html', {'form': form, 'accion': 'Editar'})

@login_required
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
