from django import forms
from .models import Producto

# Formulario para añadir stock
class AnadirStockForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=Producto.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    cantidad = forms.DecimalField(min_value=0.001, decimal_places=3, max_digits=10, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}))


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'codigo_barra',
            'nombre',
            'categoria',
            'tipo_producto',
            'unidad_base',
            'stock_actual_base',
            'stock_minimo',
            'precio_compra',
            'precio_venta',
            'unidades_por_pack',
            'kg_por_caja',
            'activo',
        ]

        widgets = {
            'codigo_barra': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'tipo_producto': forms.Select(attrs={'class': 'form-select'}),
            'unidad_base': forms.Select(attrs={'class': 'form-select'}),
            'stock_actual_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'precio_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unidades_por_pack': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'kg_por_caja': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow unidad_base to be omitted from POST when the client disables it (we set a sensible default in clean())
        self.fields['unidad_base'].required = False

    def clean(self):
        cleaned = super().clean()
        precio_compra = cleaned.get('precio_compra')
        precio_venta = cleaned.get('precio_venta')
        tipo = cleaned.get('tipo_producto')
        unidades_por_pack = cleaned.get('unidades_por_pack')
        kg_por_caja = cleaned.get('kg_por_caja')

        # Permitimos que el precio de venta sea menor al de compra desde la UI;
        # la validación previa que impedía esto se ha eliminado para no bloquear el guardado.

        if tipo == 'PACK' and not unidades_por_pack:
            self.add_error('unidades_por_pack', 'Este campo es requerido para productos tipo PACK.')
        if tipo == 'GRANEL' and not kg_por_caja:
            self.add_error('kg_por_caja', 'Este campo es requerido para productos tipo GRANEL/CAJA.')

        # Defaults: if tipo es UNITARIO, asumimos unidad_base = 'UNIDAD'; si GRANEL, unidad_base = 'KG'
        unidad_base = cleaned.get('unidad_base')
        if tipo == 'UNITARIO':
            cleaned['unidad_base'] = 'UNIDAD'
        elif tipo == 'GRANEL' and not unidad_base:
            cleaned['unidad_base'] = 'KG'
        # For PACK, enforce unidad_base at clean time (user should select it when visible)
        if tipo == 'PACK' and not cleaned.get('unidad_base'):
            self.add_error('unidad_base', 'La unidad de venta es requerida para productos tipo PACK.')

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance