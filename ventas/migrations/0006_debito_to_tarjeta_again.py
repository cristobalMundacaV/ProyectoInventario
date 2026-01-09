"""Data migration: convert metodo_pago='DEBITO' -> 'TARJETA'.

This restores 'TARJETA' as the canonical stored value.
The migration is reversible.

Note: Older migration 0002 also converted DEBITO->TARJETA, but if 0005 previously
converted TARJETA->DEBITO, this ensures existing rows are brought back.
"""

from django.db import migrations


def forwards_func(apps, schema_editor):
    Venta = apps.get_model('ventas', 'Venta')
    Venta.objects.filter(metodo_pago='DEBITO').update(metodo_pago='TARJETA')


def backwards_func(apps, schema_editor):
    Venta = apps.get_model('ventas', 'Venta')
    Venta.objects.filter(metodo_pago='TARJETA').update(metodo_pago='DEBITO')


class Migration(migrations.Migration):

    dependencies = [
        ('ventas', '0005_tarjeta_to_debito'),
    ]

    operations = [
        migrations.RunPython(forwards_func, backwards_func),
    ]
