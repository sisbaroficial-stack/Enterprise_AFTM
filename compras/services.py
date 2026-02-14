import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Avg, Count
from decimal import Decimal, ROUND_HALF_UP
from .models import SugerenciaCompra, ConfiguracionCompras, CachePrediccion
from django.db import models
from django.db.models.functions import TruncDate

# IA
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

from inventario.models import Producto, InventarioSucursal, MovimientoInventario


class ServicioPrediccionIA:
    """
    Servicio de predicción de ventas usando Prophet (IA)
    """
    
    def __init__(self, producto, sucursal=None, dias_historico=90):
        self.producto = producto
        self.sucursal = sucursal
        self.dias_historico = dias_historico
        
    def obtener_historico_ventas(self):
        """
        CORREGIDO: Ahora suma correctamente las cantidades vendidas por día
        """
        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=self.dias_historico)

        movimientos = MovimientoInventario.objects.filter(
            producto=self.producto,
            tipo='SALIDA',
            motivo='VENTA',
            fecha__gte=fecha_inicio
        )

        if self.sucursal:
            movimientos = movimientos.filter(sucursal=self.sucursal)

        # CORRECCIÓN: Usar Sum('cantidad') correctamente
        ventas_por_dia = (
            movimientos
            .annotate(dia=TruncDate('fecha'))
            .values('dia')
            .annotate(total=Sum('cantidad'))  # Suma las CANTIDADES, no cuenta registros
            .order_by('dia')
        )

        # Convertir a diccionario, manejando None
        ventas_dict = {
            v['dia']: float(v['total'] or 0)  # Proteger contra None
            for v in ventas_por_dia
        }

        # Crear historico completo con todos los días
        historico_completo = []
        dia_actual = fecha_inicio.date()
        fecha_fin_date = fecha_fin.date()

        while dia_actual <= fecha_fin_date:
            historico_completo.append({
                'dia': dia_actual,
                'total': ventas_dict.get(dia_actual, 0.0)
            })
            dia_actual += timedelta(days=1)

        return historico_completo

    def predecir_ventas_30_dias(self):
        """
        CORREGIDO: Manejo mejorado de outliers y validaciones
        """
        # ======================
        # CACHE PRIMERO
        # ======================
        cache = CachePrediccion.objects.filter(
            producto=self.producto,
            sucursal=self.sucursal
        ).first()

        if cache and cache.fecha_calculo:
            horas = (timezone.now() - cache.fecha_calculo).total_seconds() / 3600
            if horas < 12:
                return cache.prediccion, float(cache.confianza), cache.tendencia

        # ======================
        # SI NO HAY CACHE → IA
        # ======================
        if not PROPHET_AVAILABLE:
            return self._prediccion_simple()

        historico = self.obtener_historico_ventas()

        if len(historico) < 7:
            return self._prediccion_simple()

        try:
            # Crear DataFrame
            df = pd.DataFrame(historico)
            df.columns = ['ds', 'y']
            df['ds'] = pd.to_datetime(df['ds'])

            # CORRECCIÓN: Filtrado de outliers más inteligente
            ventas = df['y'].values
            ventas_positivas = ventas[ventas > 0]

            # Solo filtrar outliers si hay suficientes datos
            if len(ventas_positivas) >= 10:
                q1 = np.percentile(ventas_positivas, 25)
                q3 = np.percentile(ventas_positivas, 75)
                iqr = q3 - q1

                # Usar límites menos agresivos (3 * IQR en lugar de 1.5)
                lim_inf = max(0, q1 - 3 * iqr)
                lim_sup = q3 + 3 * iqr

                df_filtrado = df[(df['y'] >= lim_inf) & (df['y'] <= lim_sup)]
                
                # Solo usar filtrado si no eliminó demasiados datos
                if len(df_filtrado) >= len(df) * 0.7:  # Al menos 70% de datos
                    df = df_filtrado

            # Verificar que aún tengamos suficientes datos
            if len(df) < 5:
                print(f"⚠️ Muy pocos datos después de filtrar: {len(df)}")
                return self._prediccion_simple()

            # Modelo Prophet con parámetros ajustados
            modelo = Prophet(
                daily_seasonality=False,  # Desactivar para evitar overfitting
                weekly_seasonality=True,
                yearly_seasonality=False,
                changepoint_prior_scale=0.05,
                seasonality_mode='multiplicative'  # Mejor para ventas
            )

            # Silenciar warnings de Prophet
            import logging
            logging.getLogger('prophet').setLevel(logging.ERROR)
            
            modelo.fit(df)

            # Predecir
            futuro = modelo.make_future_dataframe(periods=30)
            forecast = modelo.predict(futuro)

            # Obtener predicción para próximos 30 días
            prediccion_30_dias = forecast.tail(30)['yhat'].sum()
            prediccion_30_dias = max(0, int(prediccion_30_dias))

            # Calcular confianza basada en el intervalo de predicción
            intervalos = forecast.tail(30)
            error_relativo = np.mean(
                np.abs(intervalos['yhat_upper'] - intervalos['yhat_lower']) / 
                np.maximum(intervalos['yhat'], 1)
            )
            
            confianza = max(10, min(95, 100 - (error_relativo * 50)))

            # Determinar tendencia
            tendencia_reciente = forecast.tail(30)['trend'].mean()
            tendencia_anterior = forecast.head(max(1, len(df)))['trend'].mean()

            if tendencia_reciente > tendencia_anterior * 1.15:
                tendencia = 'CRECIENTE'
            elif tendencia_reciente < tendencia_anterior * 0.85:
                tendencia = 'DECRECIENTE'
            else:
                tendencia = 'ESTABLE'

            print(f"✅ Predicción IA exitosa: {prediccion_30_dias} unidades (confianza: {confianza:.1f}%)")

            # ======================
            # GUARDAR CACHE
            # ======================
            CachePrediccion.objects.update_or_create(
                producto=self.producto,
                sucursal=self.sucursal,
                defaults={
                    'prediccion': prediccion_30_dias,
                    'confianza': confianza,
                    'tendencia': tendencia,
                    'fecha_calculo': timezone.now()
                }
            )

            return prediccion_30_dias, confianza, tendencia

        except Exception as e:
            print(f"❌ Error en Prophet: {e}")
            import traceback
            traceback.print_exc()
            return self._prediccion_simple()

    def _prediccion_simple(self):
        """
        CORREGIDO: Predicción de respaldo más robusta
        """
        historico = self.obtener_historico_ventas()

        if not historico:
            print("⚠️ Sin datos históricos")
            return 0, 50.0, 'ESTABLE'

        ventas = np.array([float(h['total']) for h in historico])
        ventas_positivas = ventas[ventas > 0]

        if len(ventas_positivas) == 0:
            print("⚠️ Sin ventas en el período")
            return 0, 50.0, 'ESTABLE'

        # CORRECCIÓN: Filtrado de outliers solo si hay suficientes datos
        if len(ventas_positivas) >= 10:
            q1 = np.percentile(ventas_positivas, 25)
            q3 = np.percentile(ventas_positivas, 75)
            iqr = q3 - q1

            lim_inf = max(0, q1 - 2 * iqr)  # Menos agresivo
            lim_sup = q3 + 2 * iqr

            ventas_filtradas = ventas[(ventas >= lim_inf) & (ventas <= lim_sup)]
            
            # Solo usar si no eliminó demasiado
            if len(ventas_filtradas) >= len(ventas) * 0.6:
                ventas = ventas_filtradas

        # Si quedó vacío, usar ventas positivas originales
        if len(ventas) == 0:
            ventas = ventas_positivas

        # Promedio ponderado (más peso a datos recientes)
        if len(ventas) > 1:
            pesos = np.arange(1, len(ventas) + 1)
            promedio_diario = np.average(ventas, weights=pesos)
        else:
            promedio_diario = np.mean(ventas)

        # Calcular tendencia
        if len(ventas) >= 3:
            x = np.arange(len(ventas))
            pendiente = np.polyfit(x, ventas, 1)[0]
            
            if pendiente > promedio_diario * 0.05:  # >5% de crecimiento
                tendencia = 'CRECIENTE'
            elif pendiente < -promedio_diario * 0.05:  # >5% de caída
                tendencia = 'DECRECIENTE'
            else:
                tendencia = 'ESTABLE'
        else:
            pendiente = 0
            tendencia = 'ESTABLE'

        # Predicción para 30 días
        prediccion = max(0, int(promedio_diario * 30))

        # Confianza basada en cantidad de datos
        confianza = min(85.0, 40 + len(ventas_positivas) * 2)

        print(f"📊 Predicción simple: {prediccion} unidades (promedio diario: {promedio_diario:.1f})")

        return prediccion, confianza, tendencia


class ServicioSugerenciasCompra:
    """
    Servicio principal para generar sugerencias de compra
    """
    
    def __init__(self, sucursal=None, usuario=None):
        self.sucursal = sucursal
        self.usuario = usuario
        self.config = self._obtener_configuracion()
    
    def _obtener_configuracion(self):
        """Obtiene o crea la configuración"""
        config, created = ConfiguracionCompras.objects.get_or_create(
            pk=1,
            defaults={
                'dias_cobertura_default': 30,
                'stock_seguridad_porcentaje': 20,
                'dias_analisis_historico': 90,
            }
        )
        return config
    
    def generar_sugerencias_todas(self):
        """Genera sugerencias para todos los productos activos"""
        if self.sucursal:
            SugerenciaCompra.objects.filter(
                sucursal=self.sucursal
            ).delete()
        
        if self.sucursal:
            inventarios = InventarioSucursal.objects.filter(
                sucursal=self.sucursal,
                producto__activo=True
            ).select_related('producto', 'producto__proveedor')
        else:
            inventarios = InventarioSucursal.objects.filter(
                producto__activo=True
            ).select_related('producto', 'producto__proveedor', 'sucursal')
        
        sugerencias_creadas = []
        
        for inv in inventarios:
            sugerencia = self.generar_sugerencia_producto(inv)
            if sugerencia:
                sugerencias_creadas.append(sugerencia)
        
        return sugerencias_creadas
    
    def generar_sugerencia_producto(self, inventario):
        """Genera sugerencia para un producto específico"""
        producto = inventario.producto
        sucursal = inventario.sucursal if hasattr(inventario, 'sucursal') else None
        clase_abc = producto.clase_abc or 'C'
        
        # 1. Análisis histórico
        servicio_ia = ServicioPrediccionIA(
            producto, 
            sucursal, 
            self.config.dias_analisis_historico
        )
        
        historico = servicio_ia.obtener_historico_ventas()
        
        if not historico:
            return None  # Sin ventas, no generar sugerencia
        
        # 2. Promedio ventas diarias
        total_ventas = sum(h['total'] for h in historico)
        dias_con_datos = len(historico)
        promedio_diario = Decimal(str(total_ventas)) / Decimal(str(max(dias_con_datos, 1)))
        
        # ✅ NUEVA VALIDACIÓN: Si no hay ventas, no generar sugerencia
        if promedio_diario == 0:
            print(f"⚠️ Producto {producto.nombre} sin ventas en {self.config.dias_analisis_historico} días - omitido")
            return None  # No generar sugerencia para productos sin movimiento

        # 3. Predicción IA
        if self.config.habilitar_ia:
            prediccion, confianza, tendencia = servicio_ia.predecir_ventas_30_dias()
        else:
            prediccion = int(promedio_diario * 30)
            confianza = 60.0
            tendencia = 'ESTABLE'
        
        # 4. Días de stock restante
        # ✅ CORREGIDO: Ya no retorna 999, la validación arriba lo previene
        dias_restantes = Decimal(str(inventario.cantidad)) / promedio_diario
        
        # 5. Punto de reorden
        dias_entrega = producto.proveedor.dias_entrega if producto.proveedor else 7
        porcentaje_seguridad = Decimal(str(self.config.stock_seguridad_porcentaje))

        # Ajustar según clase ABC
        if producto.clase_abc == 'A':
            porcentaje_seguridad *= Decimal("1.5")
        elif clase_abc == 'C':
            porcentaje_seguridad *= Decimal("0.7")

        stock_seguridad = int(
            promedio_diario * porcentaje_seguridad / Decimal("100")
        )

        punto_reorden = int(
            (promedio_diario * Decimal(str(dias_entrega))) + Decimal(str(stock_seguridad))
        )

        # 6. Cantidad sugerida
        # Ajustar cobertura según clase ABC
        if clase_abc == 'A':
            dias_cobertura = Decimal(str(self.config.dias_cobertura_default)) * Decimal("1.5")
        elif clase_abc == 'B':
            dias_cobertura = Decimal(str(self.config.dias_cobertura_default))
        else:
            dias_cobertura = Decimal(str(self.config.dias_cobertura_default)) * Decimal("0.7")

        demanda_periodo = int(promedio_diario * dias_cobertura)
        cantidad_sugerida = max(0, demanda_periodo - inventario.cantidad)
        
        # Ajustar por tendencia
        if tendencia == 'CRECIENTE':
            cantidad_sugerida = int(Decimal(cantidad_sugerida) * Decimal("1.2"))
        elif tendencia == 'DECRECIENTE':
            cantidad_sugerida = int(Decimal(cantidad_sugerida) * Decimal("0.8"))
        
        # 7. Determinar urgencia
        if dias_restantes <= self.config.umbral_urgente_dias:
            urgencia = 'URGENTE'
            razon = f"Stock crítico. Solo quedan {dias_restantes:.1f} días de inventario."
        elif dias_restantes <= self.config.umbral_alta_dias:
            urgencia = 'ALTA'
            razon = f"Stock bajo. Quedan {dias_restantes:.1f} días de inventario."
        elif dias_restantes <= self.config.umbral_media_dias:
            urgencia = 'MEDIA'
            razon = f"Stock aceptable para {dias_restantes:.1f} días más."
        else:
            urgencia = 'BAJA'
            razon = f"Stock suficiente para {dias_restantes:.1f} días."
        
        # 8. Crear sugerencia
        sugerencia = SugerenciaCompra.objects.create(
            producto=producto,
            sucursal=sucursal,
            stock_actual=inventario.cantidad,
            stock_minimo=inventario.cantidad_minima,
            promedio_ventas_diarias=promedio_diario,
            dias_stock_restante=dias_restantes,
            prediccion_proximos_30_dias=prediccion,
            tendencia=tendencia,
            cantidad_sugerida=cantidad_sugerida,
            punto_reorden=punto_reorden,
            urgencia=urgencia,
            costo_unitario=producto.precio_compra,
            proveedor_sugerido=producto.proveedor,
            generado_por=self.usuario,
            razon=razon,
            confianza_ia=Decimal(str(confianza))
        )
        
        return sugerencia