"""
Script para crear datos de prueba CORRECTOS para la IA de predicción
Ejecutar: python manage.py shell < crear_datos_prueba.py
"""

from django.utils import timezone
from datetime import timedelta, time
from inventario.models import Producto, Sucursal, MovimientoInventario
from compras.models import CachePrediccion
import random

print("=" * 60)
print("CREANDO DATOS DE PRUEBA PARA IA")
print("=" * 60)

# 1. Obtener producto y sucursal
p = Producto.objects.first()
s = Sucursal.objects.first()

if not p or not s:
    print("❌ Error: No hay productos o sucursales")
    exit()

print(f"\n📦 Producto: {p}")
print(f"🏢 Sucursal: {s}")

# 2. LIMPIAR datos anteriores
print("\n🧹 Limpiando datos anteriores...")
MovimientoInventario.objects.filter(
    producto=p,
    sucursal=s,
    tipo='SALIDA',
    motivo='VENTA'
).delete()

CachePrediccion.objects.filter(
    producto=p,
    sucursal=s
).delete()

print("✅ Datos anteriores eliminados")

# 3. CREAR datos distribuidos CORRECTAMENTE en 90 días
print("\n📊 Creando 90 días de ventas...")

hoy = timezone.now()
movimientos_creados = 0

for dias_atras in range(90):
    # Calcular fecha EXACTA del día (sin hora aleatoria)
    fecha_dia = hoy - timedelta(days=dias_atras)
    # Establecer hora fija (12:00 PM) para que todos caigan en días diferentes
    fecha_dia = fecha_dia.replace(hour=12, minute=0, second=0, microsecond=0)
    
    # Simular ventas realistas:
    # - Lunes a Viernes: más ventas
    # - Fines de semana: menos ventas
    # - Variabilidad aleatoria
    dia_semana = fecha_dia.weekday()  # 0=Lunes, 6=Domingo
    
    if dia_semana < 5:  # Lunes a Viernes
        ventas_base = random.randint(15, 30)
    else:  # Fin de semana
        ventas_base = random.randint(5, 15)
    
    # Añadir tendencia creciente (simular negocio en crecimiento)
    tendencia = int((90 - dias_atras) * 0.1)  # Crece con el tiempo
    
    # Añadir estacionalidad mensual
    dia_mes = fecha_dia.day
    if 20 <= dia_mes <= 31:  # Fin de mes
        estacionalidad = random.randint(5, 10)
    else:
        estacionalidad = 0
    
    cantidad_total = ventas_base + tendencia + estacionalidad
    
    # Crear 1-3 movimientos por día para simular múltiples transacciones
    num_transacciones = random.randint(1, 3)
    
    for trans in range(num_transacciones):
        cantidad_transaccion = cantidad_total // num_transacciones
        if trans == num_transacciones - 1:  # Última transacción lleva el resto
            cantidad_transaccion = cantidad_total - (cantidad_transaccion * (num_transacciones - 1))
        
        if cantidad_transaccion > 0:
            # Añadir minutos aleatorios para diferenciar transacciones del mismo día
            fecha_transaccion = fecha_dia + timedelta(minutes=random.randint(0, 480))
            
            MovimientoInventario.objects.create(
                producto=p,
                sucursal=s,
                tipo='SALIDA',
                motivo='VENTA',
                cantidad=cantidad_transaccion,
                fecha=fecha_transaccion
            )
            movimientos_creados += 1

print(f"✅ {movimientos_creados} movimientos creados en 90 días")

# 4. VERIFICAR distribución
print("\n🔍 Verificando distribución...")

from django.db.models import Sum, Count
from django.db.models.functions import TruncDate

ventas_por_dia = list(
    MovimientoInventario.objects.filter(
        producto=p,
        sucursal=s,
        tipo='SALIDA',
        motivo='VENTA'
    ).annotate(
        dia=TruncDate('fecha')
    ).values('dia').annotate(
        num_movimientos=Count('id'),
        total_cantidad=Sum('cantidad')
    ).order_by('-dia')[:10]
)

print(f"\nÚltimos 10 días con ventas:")
for v in ventas_por_dia:
    print(f"  {v['dia']}: {v['num_movimientos']} movimientos, {v['total_cantidad']} unidades")

total_dias = MovimientoInventario.objects.filter(
    producto=p,
    sucursal=s,
    tipo='SALIDA',
    motivo='VENTA'
).annotate(
    dia=TruncDate('fecha')
).values('dia').distinct().count()

total_unidades = MovimientoInventario.objects.filter(
    producto=p,
    sucursal=s,
    tipo='SALIDA',
    motivo='VENTA'
).aggregate(Sum('cantidad'))['cantidad__sum']

promedio_diario = total_unidades / total_dias if total_dias > 0 else 0

print(f"\n📈 Resumen:")
print(f"  Total días con ventas: {total_dias}")
print(f"  Total unidades vendidas: {total_unidades}")
print(f"  Promedio diario: {promedio_diario:.2f} unidades")

# 5. PROBAR PREDICCIÓN
print("\n" + "=" * 60)
print("PROBANDO PREDICCIÓN IA")
print("=" * 60)

from compras.services import ServicioPrediccionIA

ia = ServicioPrediccionIA(p, s)
prediccion, confianza, tendencia = ia.predecir_ventas_30_dias()

print(f"\n✅ RESULTADO:")
print(f"  Predicción próximos 30 días: {prediccion} unidades")
print(f"  Confianza: {confianza:.1f}%")
print(f"  Tendencia: {tendencia}")

# Validar resultado
if prediccion > 0:
    print(f"\n🎉 ¡ÉXITO! La predicción es razonable")
    print(f"  Promedio diario histórico: {promedio_diario:.2f}")
    print(f"  Promedio diario predicho: {prediccion / 30:.2f}")
else:
    print(f"\n❌ PROBLEMA: Predicción = 0")

print("\n" + "=" * 60)
print("PROCESO COMPLETADO")
print("=" * 60)