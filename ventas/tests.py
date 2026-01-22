from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from caja.models import Caja
from inventario.models import Producto, Categoria
from decimal import Decimal
from django.utils import timezone
from django.utils.dateformat import format as date_format
import json


class VentaMenuTest(TestCase):
    def test_venta_menu_links_exist(self):
        # login required for home view
        User = get_user_model()
        user = User.objects.create_user(username='u', password='x')
        encargado, _ = Group.objects.get_or_create(name='Encargado')
        user.groups.add(encargado)
        self.client.force_login(user)
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Ventas', resp.content)


class VentaCreateTest(TestCase):
    def setUp(self):
        User = get_user_model()
        # create a simple auth user
        self.user = User.objects.create_user(username='testuser', password='x', first_name='Test')
        encargado, _ = Group.objects.get_or_create(name='Encargado')
        self.user.groups.add(encargado)
        self.caja = Caja.objects.create(
            fecha=timezone.now().date(),
            monto_inicial=0,
            total_vendido=0,
            total_efectivo=0,
            total_debito=0,
            total_transferencia=0,
            ganancia_diaria=0,
            hora_apertura=timezone.now(),
            abierta_por=self.user
        )
        # create product and a presentacion (the sale form uses Presentacion)
        self.categoria = Categoria.objects.create(nombre='Cat')
        self.product = Producto.objects.create(
            codigo_barra='0001',
            nombre='Producto Test',
            categoria=self.categoria,
            tipo_producto='UNITARIO',
            unidad_base='UNIDAD',
            stock_actual_base=Decimal('10'),
            stock_minimo=Decimal('1'),
            precio_compra=Decimal('1.00'),
            precio_venta=Decimal('2.00'),
            margen_ganancia=Decimal('100')
        )
        # ensure client is authenticated for views that use request.user
        self.client.force_login(self.user)

    def test_venta_single_line_descuenta_stock(self):
        url = reverse('venta_create')
        data = {
            'metodo_pago': 'EFECTIVO',
            'usuario': str(self.user.id),
            'caja': str(self.caja.id),
            # formset management
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            # line 0 - use producto id
            'form-0-producto': str(self.product.id),
            'form-0-unidad_venta': 'UNIDAD',
            'form-0-cantidad_ingresada': '2',
        }
        resp = self.client.post(url, data, follow=True)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_actual_base, Decimal('8'))

    def test_venta_insuficiente_stock(self):
        url = reverse('venta_create')
        data = {
            'metodo_pago': 'EFECTIVO',
            'usuario': str(self.user.id),
            'caja': str(self.caja.id),
            # formset management
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            # line 0
            'form-0-producto': str(self.product.id),
            'form-0-unidad_venta': 'UNIDAD',
            'form-0-cantidad_ingresada': '20',
        }
        resp = self.client.post(url, data, follow=True)
        self.product.refresh_from_db()
        # stock should not have changed
        self.assertEqual(self.product.stock_actual_base, Decimal('10'))
        # response should include error message
        self.assertContains(resp, 'Stock insuficiente')

    def test_agregar_producto_ajax_no_acepta_id(self):
        url = reverse('agregar_producto_ajax')
        payload = {'codigo': str(self.product.id), 'cantidad': 1}
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 404)
        data = resp.json()
        self.assertFalse(data.get('ok'))

    def test_granel_ingreso_y_ventas_actualiza_stock_correcto(self):
        """Flujo completo:
        - Crear producto GRANEL (unidad base KG)
        - Ingresar stock mediante ingreso_stock_create
        - Vender en KG
        - Verificar que el stock final sea el esperado
        """
        granel = Producto.objects.create(
            codigo_barra='G001',
            nombre='Harina Granel',
            categoria=self.categoria,
            tipo_producto='GRANEL',
            unidad_base='KG',
            kg_por_caja=Decimal('25.000'),
            stock_actual_base=Decimal('0.000'),
            stock_minimo=Decimal('1.000'),
            precio_compra=Decimal('1000.00'),
            precio_venta=Decimal('1500.00'),
            margen_ganancia=Decimal('0.00'),
        )

        # 1) Ingreso stock +10.000 kg
        ingreso_url = reverse('ingreso_stock_create')
        fecha_local = date_format(timezone.localtime(timezone.now()), 'Y-m-d\\TH:i')
        ingreso_data = {
            'fecha': fecha_local,
            'tipo_documento': 'FACTURA',
            'numero_documento': 'TEST-GRANEL',
            'proveedor': 'Proveedor Test',
            'observacion': 'Ingreso para test',
            # inline formset default prefix uses related_name='detalles'
            'detalles-TOTAL_FORMS': '1',
            'detalles-INITIAL_FORMS': '0',
            'detalles-MIN_NUM_FORMS': '0',
            'detalles-MAX_NUM_FORMS': '1000',
            'detalles-0-producto': str(granel.id),
            'detalles-0-cantidad_base': '10.000',
        }
        resp = self.client.post(ingreso_url, ingreso_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        granel.refresh_from_db()
        self.assertEqual(granel.stock_actual_base, Decimal('10.000'))

        # 2) Venta en KG: 1.250 + 0.750 = 2.000 kg
        venta_url = reverse('venta_create')

        venta_data_1 = {
            'metodo_pago': 'EFECTIVO',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-producto': str(granel.id),
            'form-0-unidad_venta': 'KG',
            'form-0-cantidad_ingresada': '1.250',
        }
        resp1 = self.client.post(venta_url, venta_data_1, follow=True)
        self.assertEqual(resp1.status_code, 200)
        granel.refresh_from_db()
        self.assertEqual(granel.stock_actual_base, Decimal('8.750'))

        venta_data_2 = {
            'metodo_pago': 'EFECTIVO',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-producto': str(granel.id),
            'form-0-unidad_venta': 'KG',
            'form-0-cantidad_ingresada': '0.750',
        }
        resp2 = self.client.post(venta_url, venta_data_2, follow=True)
        self.assertEqual(resp2.status_code, 200)
        granel.refresh_from_db()
        self.assertEqual(granel.stock_actual_base, Decimal('8.000'))

    def test_granel_venta_por_caja_convierte_a_kg_y_descuenta(self):
        """Si se vende GRANEL por CAJA y hay kg_por_caja, debe convertir cajas->kg."""
        granel = Producto.objects.create(
            codigo_barra='G002',
            nombre='Azucar Granel',
            categoria=self.categoria,
            tipo_producto='GRANEL',
            unidad_base='KG',
            kg_por_caja=Decimal('12.000'),
            stock_actual_base=Decimal('0.000'),
            stock_minimo=Decimal('0.000'),
            precio_compra=Decimal('1000.00'),
            precio_venta=Decimal('1500.00'),
            margen_ganancia=Decimal('0.00'),
        )

        # Ingreso +20 kg
        ingreso_url = reverse('ingreso_stock_create')
        fecha_local = date_format(timezone.localtime(timezone.now()), 'Y-m-d\\TH:i')
        ingreso_data = {
            'fecha': fecha_local,
            'tipo_documento': 'FACTURA',
            'numero_documento': 'TEST-GRANEL-CAJA',
            'proveedor': 'Proveedor Test',
            'observacion': 'Ingreso para test',
            'detalles-TOTAL_FORMS': '1',
            'detalles-INITIAL_FORMS': '0',
            'detalles-MIN_NUM_FORMS': '0',
            'detalles-MAX_NUM_FORMS': '1000',
            'detalles-0-producto': str(granel.id),
            'detalles-0-cantidad_base': '20.000',
        }
        resp = self.client.post(ingreso_url, ingreso_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        granel.refresh_from_db()
        self.assertEqual(granel.stock_actual_base, Decimal('20.000'))

        # Venta 1 CAJA => descuenta 12 kg
        venta_url = reverse('venta_create')
        venta_data = {
            'metodo_pago': 'EFECTIVO',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-producto': str(granel.id),
            'form-0-unidad_venta': 'CAJA',
            'form-0-cantidad_ingresada': '1',
        }
        resp2 = self.client.post(venta_url, venta_data, follow=True)
        self.assertEqual(resp2.status_code, 200)
        granel.refresh_from_db()
        self.assertEqual(granel.stock_actual_base, Decimal('8.000'))
