import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('caja', '0003_alter_caja_ganancia_diaria_alter_caja_monto_inicial_and_more'),
        ('inventario', '0003_ingresostock_documento_fields'),
        ('ventas', '0006_debito_to_tarjeta_again'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Fiado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('cliente_nombre', models.CharField(max_length=120)),
                ('cliente_telefono', models.CharField(blank=True, max_length=30)),
                ('cliente_rut', models.CharField(blank=True, max_length=20)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('saldo', models.DecimalField(decimal_places=2, max_digits=10)),
                ('estado', models.CharField(choices=[('ABIERTO', 'Abierto'), ('PAGADO', 'Pagado'), ('ANULADO', 'Anulado')], default='ABIERTO', max_length=10)),
                ('observacion', models.CharField(blank=True, max_length=255)),
                ('caja', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='fiados', to='caja.caja')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FiadoDetalle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad_ingresada', models.DecimalField(decimal_places=3, max_digits=10)),
                ('unidad_venta', models.CharField(max_length=10)),
                ('cantidad_base', models.DecimalField(decimal_places=3, max_digits=10)),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fiado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='ventas.fiado')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.producto')),
            ],
        ),
        migrations.CreateModel(
            name='FiadoAbono',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=10)),
                ('metodo_pago', models.CharField(choices=[('EFECTIVO', 'Efectivo'), ('TARJETA', 'Tarjeta (d\u00e9bito/cr\u00e9dito)'), ('TRANSFERENCIA', 'Transferencia')], max_length=15)),
                ('referencia', models.CharField(blank=True, max_length=60)),
                ('caja', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='abonos_fiado', to='caja.caja')),
                ('fiado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='abonos', to='ventas.fiado')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
