from uuid import uuid4


import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from inventario.models import Producto, InventarioSucursal
from categorias.models import Categoria, Subcategoria
from proveedores.models import Proveedor
from sucursales.models import Sucursal


User = get_user_model()


class Command(BaseCommand):
    help = "Genera productos masivos para pruebas"

    def add_arguments(self, parser):
        parser.add_argument(
            'cantidad',
            type=int,
            help='Cantidad de productos a crear'
        )

    def handle(self, *args, **kwargs):

        cantidad = kwargs['cantidad']

        categorias = list(Categoria.objects.all())
        proveedores = list(Proveedor.objects.all())
        sucursales = list(Sucursal.objects.filter(activa=True))
        usuario = User.objects.first()

        if not categorias:
            self.stdout.write(self.style.ERROR("No hay categorías"))
            return

        productos = []

        self.stdout.write("Generando productos...")

        for i in range(cantidad):

            codigo = f"TEST-{uuid4().hex[:8].upper()}"

            categoria = random.choice(categorias)

            subcategorias = list(
                Subcategoria.objects.filter(categoria=categoria)
            )

            subcategoria = random.choice(subcategorias) if subcategorias else None

            precio_compra = Decimal(random.randint(500, 50000))
            margen = random.randint(20, 50)
            precio_venta = precio_compra * (1 + Decimal(margen) / 100)

            producto = Producto(
                codigo=codigo,
                nombre=f"Producto Test {i}",
                categoria=categoria,
                subcategoria=subcategoria,
                proveedor=random.choice(proveedores) if proveedores else None,
                precio_compra=precio_compra,
                precio_venta=precio_venta,
                cantidad_minima=random.randint(2, 10),
                unidad_medida='UNIDAD',
                creado_por=usuario
            )

            productos.append(producto)

            # Insertar en bloques para rendimiento
            if len(productos) == 500:

                Producto.objects.bulk_create(productos)

                self.crear_inventarios(productos, sucursales)

                productos = []

        # Insertar restantes
        if productos:
            Producto.objects.bulk_create(productos)
            self.crear_inventarios(productos, sucursales)

        self.stdout.write(self.style.SUCCESS("Productos creados correctamente"))

    def crear_inventarios(self, productos, sucursales):

        inventarios = []

        productos_creados = Producto.objects.filter(
            codigo__startswith="TEST-"
        ).order_by('-id')[:len(productos)]

        for producto in productos_creados:

            for sucursal in sucursales:

                inventarios.append(
                    InventarioSucursal(
                        producto=producto,
                        sucursal=sucursal,
                        cantidad=random.randint(0, 50),
                        cantidad_minima=producto.cantidad_minima
                    )
                )

        InventarioSucursal.objects.bulk_create(inventarios)
