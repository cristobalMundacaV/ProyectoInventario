"""Data migration: convert metodo_pago='DEBITO' -> 'TARJETA'.

This fixes legacy records or scripts that used the old literal 'DEBITO'.
"""
from django.db import migrations


def forwards(apps, schema_editor):
    Venta = apps.get_model('ventas', 'Venta')
    Venta.objects.filter(metodo_pago='DEBITO').update(metodo_pago='TARJETA')


def backwards(apps, schema_editor):
    Venta = apps.get_model('ventas', 'Venta')
    # Revert: change TARJETA back to DEBITO for rows that were converted.
    Venta.objects.filter(metodo_pago='TARJETA').update(metodo_pago='DEBITO')


class Migration(migrations.Migration):

    dependencies = [
        ('ventas', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
