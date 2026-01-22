import os
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, time, timedelta
from random import Random
import math

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.utils import timezone  # noqa: E402

from inventario.models import Categoria, IngresoStock, IngresoStockDetalle, Producto  # noqa: E402
from ventas.models import Venta, VentaDetalle  # noqa: E402
from caja.models import Caja  # noqa: E402


categorias_info = {
    "Bebidas": "Gaseosas, jugos y agua",
    "Alimentos Secos": "Abarrotes y granel",
    "Lácteos": "Leche, quesos, yogures",
    "Aseo Hogar": "Limpieza y cuidado",
    "Snacks": "Galletas y golosinas",
    "Bazar": "Útiles varios",
}

# Asegura un usuario para que las señales de auditoría no fallen.
User = get_user_model()
if not User.objects.exists():
    User.objects.create_superuser("admin", "admin@example.com", "admin123")
user = User.objects.filter(is_superuser=True).first() or User.objects.first()

categorias = {}
for nombre, desc in categorias_info.items():
    cat, _ = Categoria.objects.get_or_create(nombre=nombre, defaults={"descripcion": desc})
    categorias[nombre] = cat

productos = [
    {
        "nombre": "Coca-Cola 1.5L",
        "codigo_barra": "7801618000153",
        "categoria": categorias["Bebidas"],
        "tipo_producto": "UNITARIO",
        "unidad_base": "UNIDAD",
        "stock_actual_base": 24,
        "stock_minimo": 8,
        "precio_compra": Decimal("1100"),
        "precio_venta": Decimal("1490"),
    },
    {
        "nombre": "Fanta Naranja 1.5L",
        "codigo_barra": "7801618000450",
        "categoria": categorias["Bebidas"],
        "tipo_producto": "UNITARIO",
        "unidad_base": "UNIDAD",
        "stock_actual_base": 18,
        "stock_minimo": 6,
        "precio_compra": Decimal("1050"),
        "precio_venta": Decimal("1450"),
    },
    {
        "nombre": "Cerveza lata pack 6",
        "codigo_barra": "7802000123456",
        "categoria": categorias["Bebidas"],
        "tipo_producto": "PACK",
        "unidad_base": "PACK",
        "unidades_por_pack": 6,
        "stock_actual_base": 8,
        "stock_minimo": 3,
        "precio_compra": Decimal("4800"),
        "precio_venta": Decimal("7200"),
    },
    {
        "nombre": "Agua mineral 1.5L",
        "codigo_barra": "7802500901234",
        "categoria": categorias["Bebidas"],
        "tipo_producto": "UNITARIO",
        "unidad_base": "UNIDAD",
        "stock_actual_base": 20,
        "stock_minimo": 6,
        "precio_compra": Decimal("550"),
        "precio_venta": Decimal("900"),
    },
    {
        "nombre": "Arroz granel",
        "codigo_barra": None,
        "categoria": categorias["Alimentos Secos"],
        "tipo_producto": "GRANEL",
        "unidad_base": "KG",
        "kg_por_caja": Decimal("25.0"),
        "stock_actual_base": Decimal("12.5"),
        "stock_minimo": Decimal("5.0"),
        "precio_compra": Decimal("950"),
        "precio_venta": Decimal("1350"),
    },
    {
        "nombre": "Porotos granados granel",
        "codigo_barra": None,
        "categoria": categorias["Alimentos Secos"],
        "tipo_producto": "GRANEL",
        "unidad_base": "KG",
        "kg_por_caja": Decimal("25.0"),
        "stock_actual_base": Decimal("8.0"),
        "stock_minimo": Decimal("4.0"),
        "precio_compra": Decimal("1400"),
        "precio_venta": Decimal("1950"),
    },
    {
        "nombre": "Harina 1 kg",
        "codigo_barra": "7803000100016",
        "categoria": categorias["Alimentos Secos"],
        "tipo_producto": "UNITARIO",
        "unidad_base": "UNIDAD",
        "stock_actual_base": 30,
        "stock_minimo": 10,
        "precio_compra": Decimal("720"),
        "precio_venta": Decimal("1050"),
    },
    {
        "nombre": "Azúcar 1 kg",
        "codigo_barra": "7804000400004",
        "categoria": categorias["Alimentos Secos"],
        "tipo_producto": "UNITARIO",
        "unidad_base": "UNIDAD",
        "stock_actual_base": 26,
        "stock_minimo": 10,
        "precio_compra": Decimal("750"),
        "precio_venta": Decimal("1100"),
    },
    {
        "nombre": "Leche entera 1L",
        "codigo_barra": "7804300201234",
        "categoria": categorias["Lácteos"],
        "tipo_producto": "UNITARIO",
        "unidad_base": "UNIDAD",
        "stock_actual_base": 32,
        "stock_minimo": 12,
        "precio_compra": Decimal("780"),
        "precio_venta": Decimal("1150"),
    },
    {
        "nombre": "Queso laminado 200g",
        "codigo_barra": "7804500600678",
        "categoria": categorias["Lácteos"],
        "tipo_producto": "UNITARIO",
        "unidad_base": "UNIDAD",
        "stock_actual_base": 14,
        "stock_minimo": 6,
        "precio_compra": Decimal("1850"),
        "precio_venta": Decimal("2490"),
    },
    {
        "nombre": "Mantequilla 250g",
        "codigo_barra": "7804600700123",
        "categoria": categorias["Lácteos"],
        "tipo_producto": "UNITARIO",
        "unidad_base": "UNIDAD",
        "stock_actual_base": 10,
        "stock_minimo": 4,
        "precio_compra": Decimal("1450"),
        "precio_venta": Decimal("1990"),
    },
    {
        "nombre": "Detergente líquido 1L",
        "codigo_barra": "7805000900789",
        "categoria": categorias["Aseo Hogar"],
        "tipo_producto": "UNITARIO",
        "unidad_base": "UNIDAD",
        "stock_actual_base": 18,
        "stock_minimo": 6,
        "precio_compra": Decimal("1450"),
        "precio_venta": Decimal("2100"),
    },
    {
        "nombre": "Lavaloza 500ml",
        "codigo_barra": "7805100900456",
        "categoria": categorias["Aseo Hogar"],
        "tipo_producto": "UNITARIO",
        "unidad_base": "UNIDAD",
        "stock_actual_base": 22,
        "stock_minimo": 8,
        "precio_compra": Decimal("690"),
        "precio_venta": Decimal("1090"),
    },
    {
        "nombre": "Papel higiénico pack 4",
        "codigo_barra": "7805200900111",
        "categoria": categorias["Aseo Hogar"],
        "tipo_producto": "PACK",
        "unidad_base": "PACK",
        "unidades_por_pack": 4,
        "stock_actual_base": 16,
        "stock_minimo": 6,
        "precio_compra": Decimal("1350"),
        "precio_venta": Decimal("1990"),
    },
    {
        "nombre": "Papas fritas 140g",
        "codigo_barra": "7805400300123",
        "categoria": categorias["Snacks"],
        "tipo_producto": "UNITARIO",
        "unidad_base": "UNIDAD",
        "stock_actual_base": 28,
        "stock_minimo": 10,
        "precio_compra": Decimal("650"),
        "precio_venta": Decimal("990"),
    },
    {
        "nombre": "Chocolate de leche 90g",
        "codigo_barra": "7805500311223",
        "categoria": categorias["Snacks"],
        "tipo_producto": "UNITARIO",
        "unidad_base": "UNIDAD",
        "stock_actual_base": 20,
        "stock_minimo": 8,
        "precio_compra": Decimal("890"),
        "precio_venta": Decimal("1350"),
    },
    {
        "nombre": "Velas de cumpleaños pack 12",
        "codigo_barra": "7806000900777",
        "categoria": categorias["Bazar"],
        "tipo_producto": "UNITARIO",
        "unidad_base": "UNIDAD",
        "stock_actual_base": 12,
        "stock_minimo": 4,
        "precio_compra": Decimal("450"),
        "precio_venta": Decimal("790"),
    },
]

for data in productos:
    nombre = data.pop("nombre")
    prod, created = Producto.objects.get_or_create(nombre=nombre, defaults=data)
    if not created:
        for k, v in data.items():
            setattr(prod, k, v)
        prod.save()

print(f"Productos totales: {Producto.objects.count()}")
print("Carga inicial lista.")

# Ingresos de stock de ejemplo
productos_map = {p.nombre: p for p in Producto.objects.all()}
doc_tipos = ["FACTURA", "REMITO", "RECEPCION", "OTRO"]
proveedores = [
    "Distribuidora Central",
    "Mayorista Alimentos",
    "Lácteos del Sur",
    "Hogar Limpio Ltda",
    "Snacks Express",
    "Bazar Uno",
]

def _cantidad_para_producto(prod, i):
    if prod.tipo_producto == "GRANEL":
        return Decimal(f"{(i % 7) + 5}.0")
    if prod.unidad_base == "PACK":
        return Decimal((i % 4) + 2)
    return Decimal((i % 10) + 6)


def _crear_ingreso(detalles, numero, tipo, proveedor, obs, fecha):
    ingreso = IngresoStock.objects.create(
        fecha=fecha,
        tipo_documento=tipo,
        numero_documento=numero,
        proveedor=proveedor,
        usuario=user,
        observacion=obs,
    )
    for nombre_prod, cantidad in detalles:
        producto = productos_map.get(nombre_prod)
        if not producto:
            continue
        IngresoStockDetalle.objects.create(
            ingreso=ingreso,
            producto=producto,
            cantidad_base=cantidad,
        )


existing_ingresos = IngresoStock.objects.count()

if existing_ingresos == 0:
    # Cargas base (5 ingresos)
    ingresos_base = [
        {
            "tipo_documento": "FACTURA",
            "numero_documento": "F001-1001",
            "proveedor": "Distribuidora Central",
            "observacion": "Reposición bebidas",
            "detalles": [
                ("Coca-Cola 1.5L", Decimal("12")),
                ("Fanta Naranja 1.5L", Decimal("10")),
                ("Agua mineral 1.5L", Decimal("15")),
            ],
        },
        {
            "tipo_documento": "FACTURA",
            "numero_documento": "F001-1002",
            "proveedor": "Mayorista Alimentos",
            "observacion": "Secos y granel",
            "detalles": [
                ("Arroz granel", Decimal("20.0")),
                ("Porotos granados granel", Decimal("12.0")),
                ("Harina 1 kg", Decimal("18")),
                ("Azúcar 1 kg", Decimal("20")),
            ],
        },
        {
            "tipo_documento": "RECEPCION",
            "numero_documento": "R-2301",
            "proveedor": "Lácteos del Sur",
            "observacion": "Refrigerados",
            "detalles": [
                ("Leche entera 1L", Decimal("24")),
                ("Queso laminado 200g", Decimal("10")),
                ("Mantequilla 250g", Decimal("8")),
            ],
        },
        {
            "tipo_documento": "REMITO",
            "numero_documento": "RM-7788",
            "proveedor": "Hogar Limpio Ltda",
            "observacion": "Limpieza y papel",
            "detalles": [
                ("Detergente líquido 1L", Decimal("14")),
                ("Lavaloza 500ml", Decimal("20")),
                ("Papel higiénico pack 4", Decimal("12")),
            ],
        },
        {
            "tipo_documento": "OTRO",
            "numero_documento": "O-5599",
            "proveedor": "Snacks Express",
            "observacion": "Snacks variados",
            "detalles": [
                ("Papas fritas 140g", Decimal("30")),
                ("Chocolate de leche 90g", Decimal("18")),
                ("Cerveza lata pack 6", Decimal("6")),
                ("Velas de cumpleaños pack 12", Decimal("10")),
            ],
        },
    ]
    for ingreso_data in ingresos_base:
        _crear_ingreso(
            ingreso_data["detalles"],
            ingreso_data["numero_documento"],
            ingreso_data["tipo_documento"],
            ingreso_data["proveedor"],
            ingreso_data["observacion"],
            timezone.now(),
        )

# Crear ingresos auto hasta llegar a 100 totales
target_total = 100
current_total = IngresoStock.objects.count()
if current_total < target_total:
    prod_names = list(productos_map.keys())
    for i in range(target_total - current_total):
        idx = current_total + i
        doc_tipo = doc_tipos[idx % len(doc_tipos)]
        proveedor = proveedores[idx % len(proveedores)]
        numero = f"AUTO-{1000 + idx}"
        fecha = timezone.now() - timedelta(days=idx % 30)
        det_names = [
            prod_names[idx % len(prod_names)],
            prod_names[(idx + 5) % len(prod_names)],
            prod_names[(idx + 11) % len(prod_names)],
        ]
        detalles = []
        for name in det_names:
            prod = productos_map.get(name)
            if not prod:
                continue
            cantidad = _cantidad_para_producto(prod, idx)
            detalles.append((name, cantidad))
        _crear_ingreso(detalles, numero, doc_tipo, proveedor, "Ingreso auto", fecha)

print(f"Ingresos totales: {IngresoStock.objects.count()}")


# Ventas simuladas (50 por día hasta 5000)
ventas_target = 5000
ventas_per_day = 50
ventas_existentes = Venta.objects.count()
if ventas_existentes < ventas_target:
    rng = Random(42)
    productos_list = list(productos_map.values())
    total_por_crear = ventas_target - ventas_existentes
    days_needed = math.ceil(total_por_crear / ventas_per_day)
    start_date = timezone.now().date() - timedelta(days=days_needed - 1)

    def _precio(prod: Producto) -> Decimal:
        return Decimal(prod.precio_venta).quantize(Decimal("0.01"), ROUND_HALF_UP)

    def _cantidad_venta(prod: Producto) -> Decimal:
        if prod.tipo_producto == "GRANEL":
            return (Decimal(rng.randint(1, 4)) + Decimal("0.5")).quantize(Decimal("0.001"))
        if prod.unidad_base == "PACK":
            return Decimal(rng.randint(1, 3))
        return Decimal(rng.randint(1, 4))

    def _unidad_venta(prod: Producto) -> str:
        if prod.tipo_producto == "GRANEL":
            return "KG"
        if prod.unidad_base == "PACK":
            return "CAJA"
        return "UNIDAD"

    def _metodo_pago() -> str:
        roll = rng.random()
        if roll < 0.6:
            return "EFECTIVO"
        if roll < 0.85:
            return "TARJETA"
        return "TRANSFERENCIA"

    ventas_creadas = 0
    for day_offset in range(days_needed):
        fecha_dia = start_date + timedelta(days=day_offset)
        caja, _ = Caja.objects.get_or_create(
            fecha=fecha_dia,
            defaults={
                "monto_inicial": Decimal("50000") + Decimal(rng.randint(0, 15000)),
                "hora_apertura": timezone.make_aware(datetime.combine(fecha_dia, time(hour=8, minute=0))),
                "abierta": True,
                "abierta_por": user,
            },
        )

        ventas_dia_exist = Venta.objects.filter(fecha__date=fecha_dia).count()
        if ventas_dia_exist >= ventas_per_day:
            continue

        ventas_a_crear = min(ventas_per_day - ventas_dia_exist, ventas_target - ventas_existentes - ventas_creadas)
        total_dia = Decimal("0.00")
        total_efectivo = Decimal("0.00")
        total_tarjeta = Decimal("0.00")
        total_transferencia = Decimal("0.00")
        for _ in range(ventas_a_crear):
            n_items = rng.randint(1, 4)
            detalles = []
            total_venta = Decimal("0.00")
            for _i in range(n_items):
                prod = productos_list[rng.randrange(len(productos_list))]
                qty = _cantidad_venta(prod)
                precio = _precio(prod)
                subtotal = (precio * qty).quantize(Decimal("0.01"), ROUND_HALF_UP)
                detalles.append({
                    "producto": prod,
                    "cantidad_ingresada": qty,
                    "unidad_venta": _unidad_venta(prod),
                    "cantidad_base": qty,
                    "precio_unitario": precio,
                    "subtotal": subtotal,
                })
                total_venta += subtotal

            metodo = _metodo_pago()
            venta = Venta.objects.create(
                total=total_venta,
                metodo_pago=metodo,
                usuario=user,
                caja=caja,
            )
            rand_minutes = rng.randint(0, 660)
            hr = 9 + (rand_minutes // 60)
            mn = rand_minutes % 60
            venta.fecha = timezone.make_aware(datetime.combine(fecha_dia, time(hour=hr, minute=mn)))
            venta.save(update_fields=["fecha"])

            for det in detalles:
                VentaDetalle.objects.create(
                    venta=venta,
                    producto=det["producto"],
                    cantidad_ingresada=det["cantidad_ingresada"],
                    unidad_venta=det["unidad_venta"],
                    cantidad_base=det["cantidad_base"],
                    precio_unitario=det["precio_unitario"],
                    subtotal=det["subtotal"],
                )

            total_dia += total_venta
            if metodo == "EFECTIVO":
                total_efectivo += total_venta
            elif metodo == "TARJETA":
                total_tarjeta += total_venta
            else:
                total_transferencia += total_venta
            ventas_creadas += 1
            if ventas_existentes + ventas_creadas >= ventas_target:
                break

        if ventas_a_crear > 0:
            caja.total_vendido += total_dia
            caja.total_efectivo += total_efectivo
            caja.total_debito += total_tarjeta
            caja.total_transferencia += total_transferencia
            caja.ganancia_diaria += (total_dia * Decimal("0.22")).quantize(Decimal("0.01"), ROUND_HALF_UP)
            caja.hora_cierre = timezone.make_aware(datetime.combine(fecha_dia, time(hour=20, minute=0)))
            caja.abierta = False
            caja.cerrada_por = user
            caja.save()

        if ventas_existentes + ventas_creadas >= ventas_target:
            break

print(f"Ventas totales: {Venta.objects.count()}")
