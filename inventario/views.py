from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Producto, Categoria
from django import forms

class ProductoForm(forms.ModelForm):
	class Meta:
		model = Producto
		fields = '__all__'

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
		form = ProductoForm(request.POST)
		if form.is_valid():
			producto = form.save(commit=False)
			if producto.tipo_producto in ['PACK', 'UNITARIO']:
				producto.stock_minimo = int(producto.stock_minimo)
			producto.save()
			return redirect('producto_list')
	else:
		form = ProductoForm()
	return render(request, 'inventario/producto_form.html', {'form': form, 'accion': 'Nuevo'})

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
			return redirect('producto_list')
	else:
		form = ProductoForm(instance=producto)
	return render(request, 'inventario/producto_form.html', {'form': form, 'accion': 'Editar'})

@login_required
def producto_delete(request, pk):
	producto = get_object_or_404(Producto, pk=pk)
	if request.method == 'POST':
		producto.delete()
		return redirect('producto_list')
	return render(request, 'inventario/producto_confirm_delete.html', {'producto': producto})
