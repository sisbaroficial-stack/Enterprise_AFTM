from django.core.management.base import BaseCommand
from inventario.models import Producto, InventarioSucursal
from compras.services import ServicioPrediccionIA, ServicioSugerenciasCompra
from compras.models import SugerenciaCompra
import time
import statistics


class Command(BaseCommand):
    help = "Pruebas profundas del motor IA SISBAR"

    def handle(self, *args, **kwargs):

        self.stdout.write("\n🚀 INICIANDO TEST IA PROFUNDO\n")

        errores = []
        warnings = []

        # =====================================================
        # 1️⃣ Validar predicciones absurdas
        # =====================================================

        self.stdout.write("🔎 Validando predicciones absurdas")

        for p in Producto.objects.all():
            ia = ServicioPrediccionIA(p)
            pred, conf, tend = ia.predecir_ventas_30_dias()

            if pred < 0:
                errores.append(f"Predicción negativa en {p.nombre}")

            if pred > 1_000_000:
                warnings.append(f"Predicción exagerada en {p.nombre}: {pred}")

        # =====================================================
        # 2️⃣ Validar coherencia histórico vs predicción
        # =====================================================

        self.stdout.write("📊 Validando coherencia matemática")

        for p in Producto.objects.all():
            ia = ServicioPrediccionIA(p)
            hist = ia.obtener_historico_ventas()

            if hist:
                valores = [h['total'] for h in hist]
                promedio = sum(valores) / len(valores)

                pred, _, _ = ia.predecir_ventas_30_dias()

                if pred > promedio * 100:
                    warnings.append(f"Predicción exagerada en {p.nombre}")

        # =====================================================
        # 3️⃣ Productos sin histórico
        # =====================================================

        self.stdout.write("📦 Validando productos sin ventas")

        sin_datos = []

        for p in Producto.objects.all():
            if not ServicioPrediccionIA(p).obtener_historico_ventas():
                sin_datos.append(p.nombre)

        self.stdout.write(f"Productos sin ventas: {sin_datos}")

        # =====================================================
        # 4️⃣ Validar sugerencias negativas
        # =====================================================

        self.stdout.write("🛒 Validando sugerencias inválidas")

        servicio = ServicioSugerenciasCompra()
        sugerencias = servicio.generar_sugerencias_todas()

        for s in sugerencias:
            if s.cantidad_sugerida < 0:
                errores.append(f"Sugerencia negativa en {s.producto.nombre}")

        # =====================================================
        # 5️⃣ Validar duplicados
        # =====================================================

        self.stdout.write("🧬 Validando duplicados producto + sucursal")

        total = SugerenciaCompra.objects.count()
        unicos = SugerenciaCompra.objects.values(
            'producto_id',
            'sucursal_id'
        ).distinct().count()

        if total != unicos:
            errores.append("Existen duplicados en sugerencias")

        # =====================================================
        # 6️⃣ Validar lógica de stock
        # =====================================================

        self.stdout.write("📦 Validando lógica de reorden")

        for s in sugerencias:
            if s.stock_actual > s.punto_reorden and s.cantidad_sugerida > 0:
                warnings.append(
                    f"Sugiere comprar con stock suficiente en {s.producto.nombre}"
                )

        # =====================================================
        # 7️⃣ Detectar outliers históricos
        # =====================================================

        self.stdout.write("📈 Detectando variaciones extremas")

        for p in Producto.objects.all():
            hist = ServicioPrediccionIA(p).obtener_historico_ventas()

            if len(hist) > 2:
                valores = [h['total'] for h in hist]

                try:
                    if statistics.stdev(valores) > statistics.mean(valores) * 3:
                        warnings.append(f"Alta variación en {p.nombre}")
                except:
                    pass

        # =====================================================
        # 8️⃣ Test rendimiento
        # =====================================================

        self.stdout.write("⏱ Probando rendimiento")

        start = time.time()
        ServicioSugerenciasCompra().generar_sugerencias_todas()
        tiempo = time.time() - start

        if tiempo > 3:
            warnings.append(f"Generación lenta: {tiempo}")

        # =====================================================
        # 9️⃣ Validar multi-sucursal
        # =====================================================

        self.stdout.write("🏪 Validando multi sucursal")

        for suc in InventarioSucursal.objects.values_list(
                'sucursal_id', flat=True).distinct():

            servicio = ServicioSugerenciasCompra(sucursal=suc)
            sug = servicio.generar_sugerencias_todas()

            for s in sug:
                if s.stock_actual < 0:
                    errores.append(
                        f"Stock negativo en sucursal {suc} producto {s.producto.nombre}"
                    )

        # =====================================================
        # 🔟 Validar confianza IA
        # =====================================================

        self.stdout.write("🧠 Validando confianza")

        for p in Producto.objects.all():
            conf = ServicioPrediccionIA(p).predecir_ventas_30_dias()[1]

            if conf < 0 or conf > 100:
                errores.append(f"Confianza fuera de rango en {p.nombre}")

        # =====================================================
        # RESULTADO FINAL
        # =====================================================

        self.stdout.write("\n==============================")
        self.stdout.write("📋 RESULTADO FINAL")
        self.stdout.write("==============================")

        self.stdout.write(f"Errores: {errores}")
        self.stdout.write(f"Warnings: {warnings}")

        self.stdout.write(f"\nTotal errores: {len(errores)}")
        self.stdout.write(f"Total warnings: {len(warnings)}")

        self.stdout.write("\n🏁 TEST TERMINADO\n")
