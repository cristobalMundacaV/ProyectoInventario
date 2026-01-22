from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from inventario.models import Categoria, Producto

User = get_user_model()

class ProductoFormDefaultsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', 'tester@example.com', 'pass')
        admin, _ = Group.objects.get_or_create(name='Administrador')
        self.user.groups.add(admin)
        self.client = Client()
        self.client.force_login(self.user)
        self.cat = Categoria.objects.create(nombre='T')

    def test_unitario_defaults_unidad_base_and_allows_save(self):
        resp = self.client.post('/inventario/productos/nuevo/', {
            'codigo_barra': 'U001',
            'nombre': 'UnitarioTest',
            'categoria': self.cat.id,
            'tipo_producto': 'UNITARIO',
            # omit unidad_base on purpose
            'stock_actual_base': '1',
            'stock_minimo': '1',
            'precio_compra': '1.00',
            'precio_venta': '2.00',
            'activo': 'on'
        })
        # redirect expected on success
        self.assertIn(resp.status_code, (302, 303))
        p = Producto.objects.get(codigo_barra='U001')
        self.assertEqual(p.unidad_base, 'UNIDAD')

    def test_granel_defaults_kg_and_allows_save(self):
        resp = self.client.post('/inventario/productos/nuevo/', {
            'codigo_barra': 'G001',
            'nombre': 'GranelTest',
            'categoria': self.cat.id,
            'tipo_producto': 'GRANEL',
            # omit unidad_base
            'kg_por_caja': '10',
            'stock_actual_base': '1',
            'stock_minimo': '1',
            'precio_compra': '10.00',
            'precio_venta': '20.00',
            'activo': 'on'
        })
        self.assertIn(resp.status_code, (302, 303))
        p = Producto.objects.get(codigo_barra='G001')
        self.assertEqual(p.unidad_base, 'KG')

    def test_pack_requires_unidades_por_pack_and_unidad_base(self):
        # Missing unidades_por_pack should fail
        resp = self.client.post('/inventario/productos/nuevo/', {
            'codigo_barra': 'P001',
            'nombre': 'PackTest',
            'categoria': self.cat.id,
            'tipo_producto': 'PACK',
            'unidad_base': 'UNIDAD',
            'stock_actual_base': '1',
            'stock_minimo': '1',
            'precio_compra': '10.00',
            'precio_venta': '20.00',
            'activo': 'on'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Producto.objects.filter(codigo_barra='P001').exists())

        # Missing unidad_base should also fail
        resp2 = self.client.post('/inventario/productos/nuevo/', {
            'codigo_barra': 'P002',
            'nombre': 'PackTest2',
            'categoria': self.cat.id,
            'tipo_producto': 'PACK',
            'unidades_por_pack': '6',
            'stock_actual_base': '1',
            'stock_minimo': '1',
            'precio_compra': '10.00',
            'precio_venta': '20.00',
            'activo': 'on'
        })
        self.assertEqual(resp2.status_code, 200)
        self.assertFalse(Producto.objects.filter(codigo_barra='P002').exists())

    def test_granel_requires_kg_por_caja(self):
        resp = self.client.post('/inventario/productos/nuevo/', {
            'codigo_barra': 'G002',
            'nombre': 'GranelTest2',
            'categoria': self.cat.id,
            'tipo_producto': 'GRANEL',
            # missing kg_por_caja
            'stock_actual_base': '1',
            'stock_minimo': '1',
            'precio_compra': '10.00',
            'precio_venta': '20.00',
            'activo': 'on'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Producto.objects.filter(codigo_barra='G002').exists())

    def test_prices_must_be_greater_than_zero(self):
        resp = self.client.post('/inventario/productos/nuevo/', {
            'codigo_barra': 'U002',
            'nombre': 'UnitarioZeroPrice',
            'categoria': self.cat.id,
            'tipo_producto': 'UNITARIO',
            'stock_actual_base': '1',
            'stock_minimo': '0',
            'precio_compra': '0',
            'precio_venta': '0',
            'activo': 'on'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Producto.objects.filter(codigo_barra='U002').exists())

    def test_unlink_keeps_product_and_unlinks_sales(self):
        # Create product and a sale that references it, then unlink
        from ventas.models import Venta, VentaDetalle
        from caja.models import Caja
        from decimal import Decimal
        import datetime

        # producto_unlink is admin-only
        admin_group, _ = Group.objects.get_or_create(name='Administrador')
        self.user.groups.add(admin_group)

        p = Producto.objects.create(
            codigo_barra='F001',
            nombre='ForceDel',
            categoria=self.cat,
            tipo_producto='UNITARIO',
            unidad_base='UNIDAD',
            stock_actual_base=10,
            stock_minimo=1,
            precio_compra='1.00',
            precio_venta='10.00',
            activo=True
        )
        c = Caja.objects.create(
            fecha=datetime.date.today(),
            monto_inicial=Decimal('0.00'),
            hora_apertura=datetime.datetime.now(),
        )
        v = Venta.objects.create(metodo_pago='EFECTIVO', total=Decimal('10.00'), usuario=self.user, caja=c)
        vd = VentaDetalle.objects.create(venta=v, producto=p, cantidad_ingresada=Decimal('1'), unidad_venta='UNIDAD', cantidad_base=Decimal('1'), precio_unitario=Decimal('10.00'), subtotal=Decimal('10.00'))

        # Attempt unlink
        resp = self.client.post(f'/inventario/productos/{p.id}/desvincular/')
        self.assertIn(resp.status_code, (302, 303))
        # Product should still exist
        p.refresh_from_db()
        self.assertIsNotNone(Producto.objects.get(pk=p.id))
        # VentaDetalle should still exist but producto should be None
        vd.refresh_from_db()
        self.assertIsNone(vd.producto)
