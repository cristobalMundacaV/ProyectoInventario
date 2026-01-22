from django import forms
from django.forms import formset_factory
from inventario.models import Producto
from decimal import Decimal

class VentaForm(forms.Form):
    metodo_pago = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class':'form-select'}))

    def __init__(self, *args, **kwargs):
        metodo_choices = kwargs.pop('metodo_choices', None)
        super().__init__(*args, **kwargs)
        if metodo_choices is not None:
            self.fields['metodo_pago'].choices = metodo_choices


class VentaDetalleForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=Producto.objects.all(), widget=forms.Select(attrs={'class':'form-select'}) )
    unidad_venta = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class':'form-select'}))
    cantidad_ingresada = forms.DecimalField(widget=forms.NumberInput(attrs={'class':'form-control', 'step':'0.001'}), max_digits=10, decimal_places=3, min_value=Decimal('0.001'))

    def __init__(self, *args, **kwargs):
        unidad_choices = kwargs.pop('unidad_choices', None)
        super().__init__(*args, **kwargs)
        if unidad_choices is not None:
            self.fields['unidad_venta'].choices = unidad_choices


VentaDetalleFormSet = formset_factory(VentaDetalleForm, extra=1, min_num=1, validate_min=True, can_delete=True)


class FiadoForm(forms.Form):
    cliente_nombre = forms.CharField(max_length=120, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cliente_rut = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    observacion = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))


class FiadoDetalleForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=Producto.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    unidad_venta = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class': 'form-select'}))
    cantidad_ingresada = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
        max_digits=10,
        decimal_places=3,
        min_value=Decimal('0.001'),
    )

    def __init__(self, *args, **kwargs):
        unidad_choices = kwargs.pop('unidad_choices', None)
        super().__init__(*args, **kwargs)
        if unidad_choices is not None:
            self.fields['unidad_venta'].choices = unidad_choices


FiadoDetalleFormSet = formset_factory(FiadoDetalleForm, extra=1, min_num=1, validate_min=True, can_delete=True)


class FiadoAbonoForm(forms.Form):
    metodo_pago = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class': 'form-select'}))
    monto = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
    )
    referencia = forms.CharField(required=False, max_length=60, widget=forms.TextInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        metodo_choices = kwargs.pop('metodo_choices', None)
        super().__init__(*args, **kwargs)
        if metodo_choices is not None:
            self.fields['metodo_pago'].choices = metodo_choices
