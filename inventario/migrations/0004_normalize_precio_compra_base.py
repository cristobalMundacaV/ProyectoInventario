from decimal import Decimal

from django.db import migrations


def normalize_precio_compra_to_base(apps, schema_editor):
    Producto = apps.get_model('inventario', 'Producto')

    for p in Producto.objects.all().iterator():
        try:
            pc = Decimal(str(p.precio_compra or '0'))
        except Exception:
            continue

        # Convertir costo total -> costo base
        try:
            if p.tipo_producto == 'GRANEL' and p.kg_por_caja:
                kg = Decimal(str(p.kg_por_caja))
                if kg > 0:
                    pc = (pc / kg).quantize(Decimal('0.01'))
            elif p.tipo_producto == 'PACK' and p.unidad_base == 'UNIDAD' and p.unidades_por_pack:
                u = Decimal(str(int(p.unidades_por_pack)))
                if u > 0:
                    pc = (pc / u).quantize(Decimal('0.01'))
        except Exception:
            # Si algo falla, dejamos el valor tal como está.
            pass

        # Recalcular margen_ganancia con el costo base
        try:
            pv = Decimal(str(p.precio_venta or '0'))
            margen = (pv - pc).quantize(Decimal('0.01'))
        except Exception:
            margen = None

        update_fields = {'precio_compra': pc}
        if margen is not None:
            update_fields['margen_ganancia'] = margen

        Producto.objects.filter(pk=p.pk).update(**update_fields)


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0003_ingresostock_documento_fields'),
    ]

    operations = [
        migrations.RunPython(normalize_precio_compra_to_base, migrations.RunPython.noop),
    ]
