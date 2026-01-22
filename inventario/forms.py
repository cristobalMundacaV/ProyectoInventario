from django import forms
from django.forms.models import BaseInlineFormSet
from decimal import Decimal
from .models import Producto
from .models import IngresoStock, IngresoStockDetalle
from core.roles import is_admin

# Formulario para añadir stock
class AnadirStockForm(forms.Form):
    # Evita validación HTML5 del navegador (mensajes tipo "Please select an item...").
    use_required_attribute = False

    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={
            'required': 'Este campo es obligatorio.',
            'invalid_choice': 'Seleccione un producto válido.',
        },
        label='Producto',
    )
    cantidad = forms.DecimalField(
        min_value=0.001,
        decimal_places=3,
        max_digits=10,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
        error_messages={
            'required': 'Este campo es obligatorio.',
            'invalid': 'Ingrese un número válido.',
            'min_value': 'Asegúrese de que la cantidad sea mayor que 0.',
        },
        label='Cantidad a añadir',
    )


class ProductoForm(forms.ModelForm):
    # Evita mensajes del navegador (HTML5) como "Please fill out this field".
    # Preferimos mostrar errores controlados por Django en español.
    use_required_attribute = False

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
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Allow unidad_base to be omitted from POST when the client disables it (we set a sensible default in clean()).
        # We'll re-enable required dynamically for PACK below.
        if 'unidad_base' in self.fields:
            self.fields['unidad_base'].required = False

        # Código de barras obligatorio (no puede existir producto sin código)
        if 'codigo_barra' in self.fields:
            self.fields['codigo_barra'].required = True
            self.fields['codigo_barra'].label = 'Código de barras'
            self.fields['codigo_barra'].error_messages.update({
                'required': 'Este campo es obligatorio.',
                'unique': 'Ya existe un producto con este código de barras.',
                'null': 'Este campo es obligatorio.',
                'blank': 'Este campo es obligatorio.',
            })

        # Normalizar mensajes para que no aparezcan en inglés.
        # (Django puede usar mensajes por defecto como "This field is required." o "Enter a valid number.")
        common_messages = {
            'required': 'Este campo es obligatorio.',
            'invalid': 'Ingrese un valor válido.',
            'invalid_choice': 'Seleccione una opción válida.',
            'max_digits': 'Asegúrese de que este valor no tenga más de %(max)s dígitos en total.',
            'max_decimal_places': 'Asegúrese de que este valor no tenga más de %(max)s decimales.',
            'max_whole_digits': 'Asegúrese de que este valor no tenga más de %(max)s dígitos antes del separador decimal.',
        }
        for f in self.fields.values():
            try:
                # Sobrescribir explícitamente estas claves para evitar que queden defaults en inglés.
                f.error_messages.update(common_messages)
            except Exception:
                pass

        # Solo Administrador puede cambiar precios: ocultamos los campos del form
        # para Encargado, evitando que se rendericen o se validen.
        if user is not None and not is_admin(user):
            self.fields.pop('precio_compra', None)
            self.fields.pop('precio_venta', None)
        else:
            if 'precio_compra' in self.fields:
                self.fields['precio_compra'].help_text = (
                    'UNITARIO / PACK (vendido por PACK): ingrese el costo tal cual. '
                    'GRANEL: ingrese el costo de la caja (se guarda como costo por kg). '
                    'PACK (vendido por UNIDAD): ingrese el costo del pack (se guarda como costo por unidad).'
                )

        # Reglas de obligatoriedad por tipo_producto (para UI + validación Django).
        tipo = None
        try:
            if self.is_bound:
                tipo = (self.data.get('tipo_producto') or '').strip() or None
            else:
                tipo = getattr(self.instance, 'tipo_producto', None)
        except Exception:
            tipo = None

        if tipo == 'PACK':
            if 'unidades_por_pack' in self.fields:
                self.fields['unidades_por_pack'].required = True
                self.fields['unidades_por_pack'].error_messages.update({'required': 'Este campo es obligatorio.'})
            if 'unidad_base' in self.fields:
                self.fields['unidad_base'].required = True
                self.fields['unidad_base'].error_messages.update({'required': 'Este campo es obligatorio.'})
            if 'kg_por_caja' in self.fields:
                self.fields['kg_por_caja'].required = False
        elif tipo == 'GRANEL':
            if 'kg_por_caja' in self.fields:
                self.fields['kg_por_caja'].required = True
                self.fields['kg_por_caja'].error_messages.update({'required': 'Este campo es obligatorio.'})
            if 'unidades_por_pack' in self.fields:
                self.fields['unidades_por_pack'].required = False
            if 'unidad_base' in self.fields:
                # se completa automáticamente a KG en clean()
                self.fields['unidad_base'].required = False
        else:
            # UNITARIO (u otros): no requerir campos específicos
            if 'unidades_por_pack' in self.fields:
                self.fields['unidades_por_pack'].required = False
            if 'kg_por_caja' in self.fields:
                self.fields['kg_por_caja'].required = False

        # En edición, mostrar el costo TOTAL (caja/pack) aunque se guarde normalizado.
        try:
            self._set_precio_compra_initial_total_if_needed()
        except Exception:
            pass

    def clean_codigo_barra(self):
        codigo = self.cleaned_data.get('codigo_barra')
        if codigo is None:
            return codigo
        codigo = str(codigo).strip()
        if not codigo:
            raise forms.ValidationError('Este campo es obligatorio.')
        return codigo

    def clean(self):
        cleaned = super().clean()
        precio_compra = cleaned.get('precio_compra')
        precio_venta = cleaned.get('precio_venta')
        tipo = cleaned.get('tipo_producto')
        unidades_por_pack = cleaned.get('unidades_por_pack')
        kg_por_caja = cleaned.get('kg_por_caja')

        # Permitimos que el precio de venta sea menor al de compra desde la UI;
        # la validación previa que impedía esto se ha eliminado para no bloquear el guardado.

        if tipo == 'PACK':
            try:
                if unidades_por_pack is None or int(unidades_por_pack) <= 0:
                    self.add_error('unidades_por_pack', 'Debe ingresar un número mayor a 0 para productos tipo PACK.')
            except Exception:
                self.add_error('unidades_por_pack', 'Ingrese un número válido para productos tipo PACK.')

        if tipo == 'GRANEL':
            try:
                if kg_por_caja is None or float(kg_por_caja) <= 0:
                    self.add_error('kg_por_caja', 'Debe ingresar un número mayor a 0 para productos tipo GRANEL.')
            except Exception:
                self.add_error('kg_por_caja', 'Ingrese un número válido para productos tipo GRANEL.')

        # Reglas generales: precios deben ser mayores a 0 cuando el campo está disponible.
        # (En este proyecto, crear producto es admin-only; en edición puede haber usuarios sin permisos y el campo se oculta.)
        if 'precio_compra' in self.fields:
            try:
                if precio_compra is None:
                    self.add_error('precio_compra', 'Este campo es obligatorio.')
                elif float(precio_compra) <= 0:
                    self.add_error('precio_compra', 'Debe ser mayor a 0.')
            except Exception:
                self.add_error('precio_compra', 'Ingrese un número válido.')

        if 'precio_venta' in self.fields:
            try:
                if precio_venta is None:
                    self.add_error('precio_venta', 'Este campo es obligatorio.')
                elif float(precio_venta) <= 0:
                    self.add_error('precio_venta', 'Debe ser mayor a 0.')
            except Exception:
                self.add_error('precio_venta', 'Ingrese un número válido.')

        # Defaults: if tipo es UNITARIO, asumimos unidad_base = 'UNIDAD'; si GRANEL, unidad_base = 'KG'
        unidad_base = cleaned.get('unidad_base')
        if tipo == 'UNITARIO':
            cleaned['unidad_base'] = 'UNIDAD'
        elif tipo == 'GRANEL' and not unidad_base:
            cleaned['unidad_base'] = 'KG'
        # For PACK, enforce unidad_base at clean time (user should select it when visible)
        if tipo == 'PACK' and not cleaned.get('unidad_base'):
            self.add_error('unidad_base', 'La unidad de venta es obligatoria para productos tipo PACK.')

        # Normalización: evitar guardar datos que no aplican al tipo (reduce confusión en ediciones).
        if tipo != 'PACK':
            cleaned['unidades_por_pack'] = None
        if tipo != 'GRANEL':
            cleaned['kg_por_caja'] = None

        # Guardar precio_compra en unidad base:
        # - GRANEL: costo por KG
        # - PACK (unidad_base=UNIDAD): costo por UNIDAD
        # En el formulario el usuario ingresa el costo TOTAL (caja/pack). Esto se normaliza antes de guardar.
        if 'precio_compra' in self.fields and cleaned.get('precio_compra') is not None:
            try:
                pc = Decimal(str(cleaned.get('precio_compra')))
            except Exception:
                pc = None

            if pc is not None:
                if tipo == 'GRANEL':
                    kg_por_caja = cleaned.get('kg_por_caja')
                    try:
                        kg = Decimal(str(kg_por_caja)) if kg_por_caja is not None else None
                    except Exception:
                        kg = None
                    if kg is not None and kg > 0:
                        cleaned['precio_compra'] = (pc / kg).quantize(Decimal('0.01'))
                elif tipo == 'PACK' and cleaned.get('unidad_base') == 'UNIDAD':
                    unidades = cleaned.get('unidades_por_pack')
                    try:
                        u = Decimal(str(int(unidades))) if unidades is not None else None
                    except Exception:
                        u = None
                    if u is not None and u > 0:
                        cleaned['precio_compra'] = (pc / u).quantize(Decimal('0.01'))

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance

    def _set_precio_compra_initial_total_if_needed(self):
        """En edición, mostrar precio_compra como TOTAL (caja/pack) para evitar confusiones.

        Internamente se guarda normalizado (costo/kg o costo/unidad).
        """
        if self.is_bound:
            return
        if 'precio_compra' not in self.fields:
            return
        if not getattr(self.instance, 'pk', None):
            return

        tipo = getattr(self.instance, 'tipo_producto', None)
        try:
            pc_base = Decimal(str(getattr(self.instance, 'precio_compra', None)))
        except Exception:
            return

        if tipo == 'GRANEL':
            kg_por_caja = getattr(self.instance, 'kg_por_caja', None)
            try:
                kg = Decimal(str(kg_por_caja)) if kg_por_caja is not None else None
            except Exception:
                kg = None
            if kg is not None and kg > 0:
                self.fields['precio_compra'].label = 'Precio compra (Caja)'
                self.fields['precio_compra'].help_text = 'Se guarda automáticamente como costo por kg.'
                self.initial['precio_compra'] = f"{(pc_base * kg):.2f}"
        elif tipo == 'PACK' and getattr(self.instance, 'unidad_base', None) == 'UNIDAD':
            unidades = getattr(self.instance, 'unidades_por_pack', None)
            try:
                u = Decimal(str(int(unidades))) if unidades is not None else None
            except Exception:
                u = None
            if u is not None and u > 0:
                self.fields['precio_compra'].label = 'Precio compra (Pack)'
                self.fields['precio_compra'].help_text = 'Se guarda automáticamente como costo por unidad.'
                self.initial['precio_compra'] = f"{(pc_base * u):.2f}"


class IngresoStockForm(forms.ModelForm):
    class Meta:
        model = IngresoStock
        fields = ['fecha', 'tipo_documento', 'numero_documento', 'proveedor', 'observacion']
        widgets = {
            'fecha': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'proveedor': forms.TextInput(attrs={'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class IngresoStockDetalleForm(forms.ModelForm):
    class Meta:
        model = IngresoStockDetalle
        fields = ['producto', 'cantidad_base']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0.001'}),
        }


class IngresoStockDetalleRequiredFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        # Si hay errores por-campo, no agregamos este error extra para no confundir.
        if any(self.errors):
            return

        valid_items = 0
        for f in self.forms:
            if not hasattr(f, 'cleaned_data'):
                continue
            data = f.cleaned_data or {}
            if data.get('DELETE'):
                continue
            producto = data.get('producto')
            cantidad = data.get('cantidad_base')
            if producto is None:
                continue
            try:
                if cantidad is None or cantidad <= 0:
                    continue
            except Exception:
                continue
            valid_items += 1

        if valid_items <= 0:
            # Mostrar el error debajo del campo problemático (Producto) en vez de un
            # non_form_error general.
            if self.forms:
                self.forms[0].add_error('producto', 'Debe agregar al menos un producto al ingreso.')
            else:
                raise forms.ValidationError('Debe agregar al menos un producto al ingreso.')