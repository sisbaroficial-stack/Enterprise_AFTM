"""
SERVICIO DE ANÁLISIS CON IA - PROPHET
Predicciones, detección de anomalías y tendencias
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count
from django.utils import timezone

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("⚠️ Prophet no está instalado. Ejecuta: pip install prophet")


class AnalizadorIA:
    """
    Analizador financiero con IA usando Prophet de Meta
    """
    
    def __init__(self, sucursal=None):
        self.sucursal = sucursal
        
    def predecir_gastos_proximos_meses(self, meses=3):
        """
        Predice los gastos de los próximos N meses usando Prophet
        
        Args:
            meses (int): Número de meses a predecir
            
        Returns:
            dict: Predicciones con intervalos de confianza
        """
        if not PROPHET_AVAILABLE:
            return {
                'error': 'Prophet no está instalado',
                'predicciones': []
            }
        
        from finanzas.models import Gasto
        from django.db.models import Q
        
        # Obtener gastos históricos de los últimos 12 meses
        hace_12_meses = timezone.now() - timedelta(days=365)
        
        gastos_query = Gasto.objects.filter(
            fecha__gte=hace_12_meses,
            estado='APROBADO'
        )
        
        if self.sucursal:
            gastos_query = gastos_query.filter(
                Q(sucursal=self.sucursal) | Q(sucursal__isnull=True)
            )
        
        # Agrupar por mes
        gastos_por_dia = gastos_query.values('fecha').annotate(
            total=Sum('monto')
        ).order_by('fecha')
        
        if len(gastos_por_dia) < 10:
            return {
                'error': 'Necesitas al menos 10 registros para predicciones',
                'predicciones': []
            }
        
        # Preparar datos para Prophet
        df = pd.DataFrame(list(gastos_por_dia))
        df['ds'] = pd.to_datetime(df['fecha'])
        df['y'] = df['total'].astype(float)
        df = df[['ds', 'y']]
        
        # Entrenar modelo
        try:
            modelo = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                interval_width=0.95
            )
            modelo.fit(df)
            
            # Crear fechas futuras
            futuro = modelo.make_future_dataframe(periods=meses * 30)
            prediccion = modelo.predict(futuro)
            
            # Obtener predicciones futuras
            predicciones_futuras = prediccion[prediccion['ds'] > df['ds'].max()]
            
            # Agrupar por mes
            predicciones_futuras['mes'] = predicciones_futuras['ds'].dt.to_period('M')
            predicciones_mensuales = predicciones_futuras.groupby('mes').agg({
                'yhat': 'sum',
                'yhat_lower': 'sum',
                'yhat_upper': 'sum'
            }).reset_index()
            
            resultados = []
            for _, row in predicciones_mensuales.iterrows():
                resultados.append({
                    'mes': str(row['mes']),
                    'prediccion': float(row['yhat']),
                    'minimo': float(row['yhat_lower']),
                    'maximo': float(row['yhat_upper']),
                })
            
            return {
                'predicciones': resultados,
                'confianza': 0.95,
                'datos_historicos': len(df)
            }
            
        except Exception as e:
            return {
                'error': f'Error al entrenar modelo: {str(e)}',
                'predicciones': []
            }
    
    def detectar_anomalias_gastos(self, meses_atras=6):
        """
        Detecta gastos anormalmente altos o bajos
        
        Args:
            meses_atras (int): Meses a analizar
            
        Returns:
            list: Lista de anomalías detectadas
        """
        from finanzas.models import Gasto
        from django.db.models import Q
        
        inicio = timezone.now() - timedelta(days=meses_atras * 30)
        
        gastos_query = Gasto.objects.filter(
            fecha__gte=inicio,
            estado='APROBADO'
        )
        
        if self.sucursal:
            gastos_query = gastos_query.filter(
                Q(sucursal=self.sucursal) | Q(sucursal__isnull=True)
            )
        
        # Analizar por categoría
        from finanzas.models import CategoriaGasto
        categorias = CategoriaGasto.objects.filter(activa=True)
        
        anomalias = []
        
        for categoria in categorias:
            gastos_cat = gastos_query.filter(categoria=categoria)
            
            if gastos_cat.count() < 3:
                continue
            
            # Calcular estadísticas
            montos = [float(g.monto) for g in gastos_cat]
            promedio = np.mean(montos)
            desv_std = np.std(montos)
            
            # Detectar valores fuera de 2 desviaciones estándar
            umbral_superior = promedio + (2 * desv_std)
            umbral_inferior = max(0, promedio - (2 * desv_std))
            
            gastos_anomalos = gastos_cat.filter(
                monto__gt=umbral_superior
            ) | gastos_cat.filter(
                monto__lt=umbral_inferior,
                monto__gt=0
            )
            
            for gasto in gastos_anomalos:
                variacion = ((float(gasto.monto) - promedio) / promedio * 100)
                
                anomalias.append({
                    'gasto': gasto,
                    'categoria': categoria.nombre,
                    'monto': float(gasto.monto),
                    'promedio': promedio,
                    'variacion': variacion,
                    'tipo': 'alto' if gasto.monto > umbral_superior else 'bajo',
                    'fecha': gasto.fecha,
                })
        
        # Ordenar por variación absoluta
        anomalias.sort(key=lambda x: abs(x['variacion']), reverse=True)
        
        return anomalias[:10]  # Top 10 anomalías
    
    def analizar_tendencias_categorias(self, meses=6):
        """
        Analiza tendencias de gasto por categoría
        
        Returns:
            dict: Tendencias por categoría
        """
        from finanzas.models import Gasto, CategoriaGasto
        from django.db.models import Q
        
        inicio = timezone.now() - timedelta(days=meses * 30)
        
        gastos_query = Gasto.objects.filter(
            fecha__gte=inicio,
            estado='APROBADO'
        )
        
        if self.sucursal:
            gastos_query = gastos_query.filter(
                Q(sucursal=self.sucursal) | Q(sucursal__isnull=True)
            )
        
        categorias = CategoriaGasto.objects.filter(activa=True)
        tendencias = []
        
        for categoria in categorias:
            gastos_cat = gastos_query.filter(categoria=categoria)
            
            if gastos_cat.count() < 2:
                continue
            
            # Dividir en dos mitades
            total_dias = (timezone.now().date() - inicio.date()).days
            mitad = inicio + timedelta(days=total_dias // 2)
            
            primera_mitad = gastos_cat.filter(fecha__lt=mitad)
            segunda_mitad = gastos_cat.filter(fecha__gte=mitad)
            
            total_primera = primera_mitad.aggregate(Sum('monto'))['monto__sum'] or Decimal('0')
            total_segunda = segunda_mitad.aggregate(Sum('monto'))['monto__sum'] or Decimal('0')
            
            if total_primera > 0:
                variacion = ((total_segunda - total_primera) / total_primera * 100)
                
                # Determinar tendencia
                if variacion > 10:
                    tendencia = 'CRECIENTE'
                    icono = '📈'
                    color = 'danger'
                elif variacion < -10:
                    tendencia = 'DECRECIENTE'
                    icono = '📉'
                    color = 'success'
                else:
                    tendencia = 'ESTABLE'
                    icono = '➡️'
                    color = 'info'
                
                tendencias.append({
                    'categoria': categoria,
                    'tendencia': tendencia,
                    'icono': icono,
                    'color': color,
                    'variacion': float(variacion),
                    'total_reciente': float(total_segunda),
                })
        
        # Ordenar por variación
        tendencias.sort(key=lambda x: abs(x['variacion']), reverse=True)
        
        return tendencias
    
    def generar_recomendaciones(self):
        """
        Genera recomendaciones basadas en IA
        
        Returns:
            list: Lista de recomendaciones
        """
        recomendaciones = []
        
        # Detectar anomalías
        anomalias = self.detectar_anomalias_gastos(meses_atras=3)
        
        if anomalias:
            for anomalia in anomalias[:3]:  # Top 3
                if anomalia['tipo'] == 'alto':
                    recomendaciones.append({
                        'tipo': 'ALERTA',
                        'prioridad': 'ALTA',
                        'icono': '⚠️',
                        'titulo': f'Gasto elevado en {anomalia["categoria"]}',
                        'descripcion': f'Detectamos un gasto de ${anomalia["monto"]:,.0f}, '
                                     f'que es {abs(anomalia["variacion"]):.0f}% mayor al promedio '
                                     f'(${anomalia["promedio"]:,.0f})',
                        'accion': 'Revisar si este gasto era necesario o se puede optimizar'
                    })
        
        # Analizar tendencias
        tendencias = self.analizar_tendencias_categorias(meses=6)
        
        for tendencia in tendencias[:2]:  # Top 2
            if tendencia['tendencia'] == 'CRECIENTE' and tendencia['variacion'] > 20:
                recomendaciones.append({
                    'tipo': 'OPTIMIZACIÓN',
                    'prioridad': 'MEDIA',
                    'icono': '💡',
                    'titulo': f'Gastos en {tendencia["categoria"].nombre} aumentando',
                    'descripcion': f'Han aumentado {tendencia["variacion"]:.0f}% en los últimos meses',
                    'accion': 'Buscar alternativas más económicas o negociar mejores precios'
                })
        
        # Predicciones
        predicciones = self.predecir_gastos_proximos_meses(meses=1)
        
        if 'predicciones' in predicciones and predicciones['predicciones']:
            proxima = predicciones['predicciones'][0]
            
            recomendaciones.append({
                'tipo': 'PREDICCIÓN',
                'prioridad': 'INFO',
                'icono': '🔮',
                'titulo': 'Proyección próximo mes',
                'descripcion': f'Gastos estimados: ${proxima["prediccion"]:,.0f} '
                             f'(rango: ${proxima["minimo"]:,.0f} - ${proxima["maximo"]:,.0f})',
                'accion': 'Planificar presupuesto considerando esta estimación'
            })
        
        return recomendaciones
    
    def calcular_scoring_salud_financiera(self):
        """
        Calcula un score de 0-100 de la salud financiera
        
        Returns:
            dict: Score y detalles
        """
        from finanzas.services.calculador_finanzas import CalculadorFinanzas
        from django.http import HttpRequest
        
        # Crear request mock
        request = HttpRequest()
        request.user = None
        request.session = {'sucursal_actual': self.sucursal.id if self.sucursal else None}
        
        # Calcular datos del mes
        ahora = timezone.now()
        calculador = CalculadorFinanzas(request)
        datos = calculador.calcular_utilidad_mes(ahora.month, ahora.year)
        
        score = 0
        detalles = []
        
        # Factor 1: Margen Neto (40 puntos)
        margen_neto = float(datos['margen_neto'])
        if margen_neto >= 25:
            puntos_margen = 40
            estado_margen = 'EXCELENTE'
        elif margen_neto >= 20:
            puntos_margen = 35
            estado_margen = 'MUY BUENO'
        elif margen_neto >= 15:
            puntos_margen = 25
            estado_margen = 'BUENO'
        elif margen_neto >= 10:
            puntos_margen = 15
            estado_margen = 'REGULAR'
        else:
            puntos_margen = 5
            estado_margen = 'MEJORABLE'
        
        score += puntos_margen
        detalles.append({
            'factor': 'Margen Neto',
            'valor': f'{margen_neto:.1f}%',
            'puntos': puntos_margen,
            'maximo': 40,
            'estado': estado_margen
        })
        
        # Factor 2: Control de Gastos (30 puntos)
        comparativa = calculador.comparar_meses(ahora.month, ahora.year, 1)
        var_gastos = float(comparativa['variaciones']['gastos'])
        
        if var_gastos < -5:  # Gastos reducidos
            puntos_gastos = 30
            estado_gastos = 'EXCELENTE'
        elif var_gastos < 0:
            puntos_gastos = 25
            estado_gastos = 'MUY BUENO'
        elif var_gastos < 5:
            puntos_gastos = 20
            estado_gastos = 'BUENO'
        elif var_gastos < 10:
            puntos_gastos = 10
            estado_gastos = 'REGULAR'
        else:
            puntos_gastos = 5
            estado_gastos = 'MEJORABLE'
        
        score += puntos_gastos
        detalles.append({
            'factor': 'Control de Gastos',
            'valor': f'{var_gastos:+.1f}%',
            'puntos': puntos_gastos,
            'maximo': 30,
            'estado': estado_gastos
        })
        
        # Factor 3: Crecimiento de Ventas (30 puntos)
        var_ventas = float(comparativa['variaciones']['ventas'])
        
        if var_ventas > 15:
            puntos_ventas = 30
            estado_ventas = 'EXCELENTE'
        elif var_ventas > 10:
            puntos_ventas = 25
            estado_ventas = 'MUY BUENO'
        elif var_ventas > 5:
            puntos_ventas = 20
            estado_ventas = 'BUENO'
        elif var_ventas > 0:
            puntos_ventas = 15
            estado_ventas = 'REGULAR'
        else:
            puntos_ventas = 5
            estado_ventas = 'MEJORABLE'
        
        score += puntos_ventas
        detalles.append({
            'factor': 'Crecimiento Ventas',
            'valor': f'{var_ventas:+.1f}%',
            'puntos': puntos_ventas,
            'maximo': 30,
            'estado': estado_ventas
        })
        
        # Clasificación general
        if score >= 90:
            clasificacion = 'EXCELENTE'
            color = 'success'
            mensaje = '¡Salud financiera excepcional!'
        elif score >= 75:
            clasificacion = 'MUY BUENO'
            color = 'info'
            mensaje = 'Salud financiera sólida'
        elif score >= 60:
            clasificacion = 'BUENO'
            color = 'primary'
            mensaje = 'Salud financiera aceptable'
        elif score >= 40:
            clasificacion = 'REGULAR'
            color = 'warning'
            mensaje = 'Hay margen de mejora'
        else:
            clasificacion = 'MEJORABLE'
            color = 'danger'
            mensaje = 'Requiere atención urgente'
        
        return {
            'score': score,
            'clasificacion': clasificacion,
            'color': color,
            'mensaje': mensaje,
            'detalles': detalles
        }