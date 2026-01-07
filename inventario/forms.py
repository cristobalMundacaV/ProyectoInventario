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
            'precio_compra': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'precio_venta': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'unidades_por_pack': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1'
            }),
            'kg_por_caja': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos condicionales según unidad_venta
        if 'unidad_venta' in self.data:
            unidad_venta = self.data.get('unidad_venta')
            if unidad_venta != 'PACK':
                self.fields['unidades_por_pack'].required = False
            if unidad_venta != 'CAJA':
                self.fields['kg_por_caja'].required = False

    def clean(self):
        cleaned = super().clean()

        precio_compra = cleaned.get('precio_compra')
        precio_venta = cleaned.get('precio_venta')
        unidad_venta = cleaned.get('unidad_venta')
        unidades_por_pack = cleaned.get('unidades_por_pack')
        kg_por_caja = cleaned.get('kg_por_caja')

        if precio_compra is not None and precio_venta is not None:
            if precio_venta < precio_compra:
                self.add_error(
                    'precio_venta',
                    'El precio de venta no puede ser menor al precio de compra.'
                )

        # Validaciones específicas por tipo de unidad
        if unidad_venta == 'PACK' and not unidades_por_pack:
            self.add_error(
                'unidades_por_pack',
                'Este campo es requerido para productos tipo PACK.'
            )

        if unidad_venta == 'CAJA' and not kg_por_caja:
            self.add_error(
                'kg_por_caja',
                'Este campo es requerido para productos tipo CAJA.'
            )

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        # El margen_ganancia se calcula automáticamente en el método save del modelo
        if commit:
            instance.save()
        return instance