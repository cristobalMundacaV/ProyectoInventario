from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from caja.models import Caja
from inventario.models import Producto, Categoria
from decimal import Decimal
from django.utils import timezone


class VentaMenuTest(TestCase):
    def test_venta_menu_links_exist(self):
        # login required for home view
        User = get_user_model()
        user = User.objects.create_user(username='u', password='x')
        self.client.force_login(user)
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Ventas', resp.content)


class VentaCreateTest(TestCase):
    def setUp(self):
        User = get_user_model()
        # create a simple auth user
        self.user = User.objects.create_user(username='testuser', password='x', first_name='Test')
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
