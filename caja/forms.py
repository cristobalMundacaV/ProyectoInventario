from django import forms
from .models import Caja

class AperturaCajaForm(forms.ModelForm):
    class Meta:
        model = Caja
        fields = ['monto_inicial']
        widgets = {
            'monto_inicial': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ingrese el monto inicial',
                    'step': '0.01',
                    'min': '0'
                }
            )
        }
        labels = {
            'monto_inicial': 'Monto Inicial'
        }
