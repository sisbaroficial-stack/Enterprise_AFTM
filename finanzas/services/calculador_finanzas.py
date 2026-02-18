"""
CALCULADOR FINANCIERO
Servicio principal para cálculos de utilidad, gastos e ingresos
Maneja modo SUCURSAL vs modo GLOBAL de forma inteligente
"""

from decimal import Decimal
from datetime import datetime
from django.db.models import Sum, Q
from django.utils import timezone

from facturas.models import Factura, DetalleFactura
from finanzas.models import Gasto, AnalisisFinanciero
from sucursales.models import Sucursal


class CalculadorFinanzas:
    """
    Calculadora inteligente que se adapta al contexto:
    - SUPER_ADMIN en modo global: calcula TODO
    - SUPER_ADMIN con sucursal: calcula esa sucursal
    - ADMIN: calcula solo su sucursal
    """
    
    def __init__(self, request):
        self.request = request
        self.user = request.user
        self.sucursal_actual = self._obtener_sucursal()
    
    def _obtener_sucursal(self):
        """
        Determina qué sucursal usar según el contexto del usuario
        Returns:
            Sucursal o None (None = modo global)
        """

        # 🔒 Protección básica
        if not self.user:
            return None

        if not hasattr(self.user, 'rol'):
            return None

        # CASO 1: SUPER_ADMIN sin sucursal seleccionada = MODO GLOBAL
        if self.user.rol == 'SUPER_ADMIN' and not self.request.session.get('sucursal_actual'):
            return None

        # CASO 2: SUPER_ADMIN con sucursal seleccionada
        if self.user.rol == 'SUPER_ADMIN' and self.request.session.get('sucursal_actual'):
            try:
                return Sucursal.objects.get(id=self.request.session['sucursal_actual'])
            except Sucursal.DoesNotExist:
                return None

        # CASO 3: ADMIN - siempre su sucursal asignada
        if self.user.rol == 'ADMIN':
            return getattr(self.user, 'sucursal', None)

        # CASO 4: Otros roles
        return getattr(self.user, 'sucursal', None)

    
    def calcular_utilidad_mes(self, mes, anio):
        """
        Calcula la utilidad neta del mes especificado
        
        Args:
            mes (int): Mes (1-12)
            anio (int): Año (ej: 2026)
        
        Returns:
            dict: Diccionario con todos los datos financieros
        """
        # ===== PASO 1: FILTRAR FACTURAS =====
        facturas_query = Factura.objects.filter(
            fecha__year=anio,
            fecha__month=mes,
            anulada=False  # Solo facturas válidas
        )
        
        # Aplicar filtro de sucursal
        if self.sucursal_actual:
            # Modo SUCURSAL específica
            facturas_query = facturas_query.filter(sucursal=self.sucursal_actual)
            sucursales_incluidas = [self.sucursal_actual]
        else:
            # Modo GLOBAL - todas las sucursales
            sucursales_incluidas = list(Sucursal.objects.filter(activa=True))
        
        # ===== PASO 2: CALCULAR INGRESOS =====
        total_ventas = sum([f.total for f in facturas_query]) or Decimal('0')
        num_facturas = facturas_query.count()
        
        # ===== PASO 3: CALCULAR COSTO DE MERCANCÍA VENDIDA =====
        costo_mercancia = Decimal('0')
        
        for factura in facturas_query:
            for detalle in factura.detalles.all():
                # Costo = precio_compra * cantidad vendida
                costo_producto = (
                    detalle.producto.precio_compra * 
                    Decimal(detalle.cantidad)
                )
                costo_mercancia += costo_producto
        
        # ===== PASO 4: CALCULAR UTILIDAD BRUTA =====
        utilidad_bruta = total_ventas - costo_mercancia
        margen_bruto = (utilidad_bruta / total_ventas * 100) if total_ventas > 0 else Decimal('0')
        
        # ===== PASO 5: CALCULAR GASTOS OPERATIVOS =====
        gastos_query = Gasto.objects.filter(
            fecha__year=anio,
            fecha__month=mes,
            estado='APROBADO'  # Solo gastos aprobados
        )
        
        if self.sucursal_actual:
            # Sucursal específica + gastos generales
            gastos_query = gastos_query.filter(
                Q(sucursal=self.sucursal_actual) |
                Q(sucursal__isnull=True)  # Gastos generales de la empresa
            )
        # else: modo global toma TODOS los gastos
        
        total_gastos = gastos_query.aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0')
        
        num_gastos = gastos_query.count()
        
        # ===== PASO 6: CALCULAR UTILIDAD NETA =====
        utilidad_neta = utilidad_bruta - total_gastos
        margen_neto = (utilidad_neta / total_ventas * 100) if total_ventas > 0 else Decimal('0')
        
        # ===== PASO 7: DESGLOSE DE GASTOS POR CATEGORÍA =====
        from finanzas.models import CategoriaGasto
        
        gastos_por_categoria = []
        categorias = CategoriaGasto.objects.filter(activa=True)
        
        for categoria in categorias:
            gastos_cat = gastos_query.filter(categoria=categoria)
            total_cat = gastos_cat.aggregate(total=Sum('monto'))['total'] or Decimal('0')
            
            if total_cat > 0:
                porcentaje = (total_cat / total_gastos * 100) if total_gastos > 0 else 0
                gastos_por_categoria.append({
                    'categoria': categoria,
                    'total': total_cat,
                    'porcentaje': porcentaje,
                    'num_gastos': gastos_cat.count(),
                })
        
        # Ordenar por monto descendente
        gastos_por_categoria.sort(key=lambda x: x['total'], reverse=True)
        
        # ===== PASO 8: RETORNAR RESULTADO COMPLETO =====
        return {
            # Ingresos
            'total_ventas': total_ventas,
            'num_facturas': num_facturas,
            
            # Costos
            'costo_mercancia': costo_mercancia,
            
            # Utilidad Bruta
            'utilidad_bruta': utilidad_bruta,
            'margen_bruto': margen_bruto,
            
            # Gastos
            'total_gastos': total_gastos,
            'num_gastos': num_gastos,
            'gastos_por_categoria': gastos_por_categoria,
            
            # Utilidad Neta
            'utilidad_neta': utilidad_neta,
            'margen_neto': margen_neto,
            
            # Contexto
            'sucursales': sucursales_incluidas,
            'es_modo_global': self.sucursal_actual is None,
            'mes': mes,
            'anio': anio,
        }
    
    def comparar_meses(self, mes_actual, anio_actual, meses_atras=1):
        """
        Compara el mes actual con meses anteriores
        
        Args:
            mes_actual (int): Mes actual
            anio_actual (int): Año actual
            meses_atras (int): Cuántos meses atrás comparar
        
        Returns:
            dict: Comparativa con variaciones
        """
        # Calcular mes anterior
        if mes_actual - meses_atras < 1:
            mes_anterior = 12 + (mes_actual - meses_atras)
            anio_anterior = anio_actual - 1
        else:
            mes_anterior = mes_actual - meses_atras
            anio_anterior = anio_actual
        
        # Obtener datos de ambos meses
        datos_actual = self.calcular_utilidad_mes(mes_actual, anio_actual)
        datos_anterior = self.calcular_utilidad_mes(mes_anterior, anio_anterior)
        
        # Calcular variaciones
        def calcular_variacion(actual, anterior):
            if anterior > 0:
                return ((actual - anterior) / anterior * 100)
            elif actual > 0:
                return Decimal('100')
            else:
                return Decimal('0')
        
        return {
            'mes_actual': datos_actual,
            'mes_anterior': datos_anterior,
            'variaciones': {
                'ventas': calcular_variacion(datos_actual['total_ventas'], datos_anterior['total_ventas']),
                'gastos': calcular_variacion(datos_actual['total_gastos'], datos_anterior['total_gastos']),
                'utilidad_neta': calcular_variacion(datos_actual['utilidad_neta'], datos_anterior['utilidad_neta']),
            }
        }
    
    def calcular_punto_equilibrio(self, mes, anio):
        """
        Calcula el punto de equilibrio del mes
        
        Returns:
            dict: Ventas necesarias para no perder
        """
        datos = self.calcular_utilidad_mes(mes, anio)
        
        # Punto de equilibrio = Costos Fijos + Costos Variables
        # Para simplificar: Costo Mercancía + Gastos
        punto_equilibrio = datos['costo_mercancia'] + datos['total_gastos']
        
        # Margen de seguridad = Ventas actuales - Punto de equilibrio
        margen_seguridad = datos['total_ventas'] - punto_equilibrio
        
        # Porcentaje de margen de seguridad
        porcentaje_margen = (margen_seguridad / datos['total_ventas'] * 100) if datos['total_ventas'] > 0 else 0
        
        return {
            'punto_equilibrio': punto_equilibrio,
            'ventas_actuales': datos['total_ventas'],
            'margen_seguridad': margen_seguridad,
            'porcentaje_margen': porcentaje_margen,
            'en_riesgo': margen_seguridad < 0,
        }
    
    def obtener_top_gastos(self, mes, anio, limite=10):
        """
        Obtiene los gastos más grandes del mes
        
        Returns:
            QuerySet: Top gastos ordenados por monto
        """
        gastos_query = Gasto.objects.filter(
            fecha__year=anio,
            fecha__month=mes,
            estado='APROBADO'
        )
        
        if self.sucursal_actual:
            gastos_query = gastos_query.filter(
                Q(sucursal=self.sucursal_actual) |
                Q(sucursal__isnull=True)
            )
        
        return gastos_query.order_by('-monto')[:limite]
    
    def guardar_analisis_cache(self, mes, anio):
        """
        Guarda el análisis en cache para no recalcular
        """
        datos = self.calcular_utilidad_mes(mes, anio)
        
        analisis, created = AnalisisFinanciero.objects.update_or_create(
            sucursal=self.sucursal_actual,
            mes=mes,
            anio=anio,
            defaults={
                'total_ventas': datos['total_ventas'],
                'costo_mercancia': datos['costo_mercancia'],
                'utilidad_bruta': datos['utilidad_bruta'],
                'total_gastos': datos['total_gastos'],
                'utilidad_neta': datos['utilidad_neta'],
                'margen_bruto': datos['margen_bruto'],
                'margen_neto': datos['margen_neto'],
            }
        )
        
        return analisis
