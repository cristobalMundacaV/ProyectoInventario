from django import forms
from .models import Producto, Presentacion


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre',
            'categoria',
            'tipo_producto',
            'unidad_base',
            'stock_actual_base',
            'stock_minimo',
        ]

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo_producto': forms.Select(attrs={
                'class': 'form-select'
            }),
            'unidad_base': forms.Select(attrs={
                'class': 'form-select'
            }),
            'stock_actual_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001'
            }),
        }

class PresentacionForm(forms.ModelForm):
    class Meta:
        model = Presentacion
        exclude = [
            'producto',
            'margen_ganancia',
        ]

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'codigo_barra': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'unidad_venta': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cantidad_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1'
            }),
            'stock_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001'
            }),
            'precio_compra': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'precio_venta': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }

    def clean(self):
        cleaned = super().clean()

        cantidad_base = cleaned.get('cantidad_base')
        precio_compra = cleaned.get('precio_compra')
        precio_venta = cleaned.get('precio_venta')

        if cantidad_base is not None and cantidad_base <= 0:
            self.add_error(
                'cantidad_base',
                'La cantidad base debe ser mayor a 0.'
            )

        if precio_compra is not None and precio_venta is not None:
            if precio_venta < precio_compra:
                self.add_error(
                    'precio_venta',
                    'El precio de venta no puede ser menor al precio de compra.'
                )

        return cleaned
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.margen_ganancia = (
            instance.precio_venta - instance.precio_compra
        )
        if commit:
            instance.save()
        return instance    