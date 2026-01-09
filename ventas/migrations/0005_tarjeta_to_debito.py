"""Data migration: convert metodo_pago='TARJETA' -> 'DEBITO'.

This aligns stored values with the current MetodoPago enum, which uses DEBITO.
The migration is reversible.
"""

from django.db import migrations


def forwards_func(apps, schema_editor):
    Venta = apps.get_model('ventas', 'Venta')
    Venta.objects.filter(metodo_pago='TARJETA').update(metodo_pago='DEBITO')


def backwards_func(apps, schema_editor):
    Venta = apps.get_model('ventas', 'Venta')
    Venta.objects.filter(metodo_pago='DEBITO').update(metodo_pago='TARJETA')


class Migration(migrations.Migration):

    dependencies = [
        ('ventas', '0004_alter_venta_total_alter_ventadetalle_cantidad_base_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards_func, backwards_func),
    ]
