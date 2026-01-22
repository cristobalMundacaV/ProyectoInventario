from django import forms
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    # Evita validación HTML5 del navegador (mensajes en inglés como
    # "Please fill out this field"). La validación la maneja Django.
    use_required_attribute = False

    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': 'Usuario o contraseña incorrectos.',
        'inactive': 'Esta cuenta está inactiva.',
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)

        # Normalizar mensajes en español en campos
        for name in ('username', 'password'):
            if name in self.fields:
                self.fields[name].error_messages.update({
                    'required': 'Este campo es obligatorio.',
                    'invalid': 'Ingrese un valor válido.',
                })

        # Clases Bootstrap
        if 'username' in self.fields:
            self.fields['username'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'username'})
        if 'password' in self.fields:
            self.fields['password'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'current-password'})
