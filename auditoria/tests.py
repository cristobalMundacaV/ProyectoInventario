from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from caja.models import Caja
from auditoria.models import Actividad
from inventario.models import Categoria

User = get_user_model()

class ActividadCajaFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', 'tester@example.com', 'pass')
        encargado, _ = Group.objects.get_or_create(name='Encargado')
        admin, _ = Group.objects.get_or_create(name='Administrador')
        self.user.groups.add(encargado)
        self.user.groups.add(admin)
        self.client = Client()
        self.client.force_login(self.user)

    def test_activities_linked_to_open_caja_and_cierre(self):
        # Open caja
        resp = self.client.post('/caja/abrir/', {'monto_inicial': '300.00'})
        self.assertEqual(resp.status_code, 302)
        caja = Caja.objects.filter(abierta=True).order_by('-hora_apertura').first()
        self.assertIsNotNone(caja)

        # Create a product
        cat, _ = Categoria.objects.get_or_create(nombre='TEST')
        resp = self.client.post('/inventario/productos/nuevo/', {
            'codigo_barra': 'T100',
            'nombre': 'ProductoTest',
            'categoria': cat.id,
            'tipo_producto': 'UNITARIO',
            'unidad_base': 'UNIDAD',
            'stock_actual_base': '5',
            'stock_minimo': '1',
            'precio_compra': '1.00',
            'precio_venta': '10.00',
            'activo': 'on'
        })
        self.assertEqual(resp.status_code, 302)

        # Create two ventas via management command
        call_command('add_ventas_large')

        # Check activities associated with caja
        actividades = Actividad.objects.filter(caja=caja)
        tipos = set(actividades.values_list('tipo_accion', flat=True))
        self.assertIn('VENTA', tipos)
        self.assertIn('APERTURA_CAJA', tipos)
        self.assertIn('CREACION_PRODUCTO', tipos)
        # Expect at least 3 activities (apertura, producto, 2 ventas)
        self.assertTrue(actividades.count() >= 4)

        # Close caja
        resp = self.client.post('/caja/cerrar/')
        self.assertEqual(resp.status_code, 302)
        caja.refresh_from_db()
        # After closing, there should be a CIERRA_CAJA activity
        self.assertTrue(Actividad.objects.filter(caja=caja, tipo_accion='CIERRE_CAJA').exists())
        # Totals should be set
        self.assertIsNotNone(caja.total_vendido)
        self.assertIsNotNone(caja.ganancia_diaria)
