"""
CALCULADORA DE NÓMINA - COLOMBIA 2026
Cálculos automáticos según normativa colombiana
"""

from decimal import Decimal
from datetime import datetime
from django.utils import timezone


class CalculadoraNomina:
    """
    Calculadora de nómina según normativa colombiana 2026
    """
    
    # Constantes Colombia 2026
    SALARIO_MINIMO = Decimal('1423500')  # Actualizar según año
    AUXILIO_TRANSPORTE = Decimal('162000')  # Actualizar según año
    
    # Porcentajes deducciones empleado
    PORCENTAJE_SALUD_EMPLEADO = Decimal('0.04')  # 4%
    PORCENTAJE_PENSION_EMPLEADO = Decimal('0.04')  # 4%
    
    # Porcentajes aportes empresa
    PORCENTAJE_SALUD_EMPRESA = Decimal('0.085')  # 8.5%
    PORCENTAJE_PENSION_EMPRESA = Decimal('0.12')  # 12%
    PORCENTAJE_ARL = Decimal('0.00522')  # 0.522% (riesgo I)
    PORCENTAJE_CAJA = Decimal('0.04')  # 4%
    PORCENTAJE_ICBF = Decimal('0.03')  # 3%
    PORCENTAJE_SENA = Decimal('0.02')  # 2%
    
    def __init__(self, empleado):
        self.empleado = empleado
    
    def calcular_nomina_mes(self, mes, anio, **kwargs):
        """
        Calcula la nómina completa de un empleado para un mes
        
        Args:
            mes (int): Mes (1-12)
            anio (int): Año
            **kwargs: Valores opcionales (horas_extras, bonificaciones, etc.)
            
        Returns:
            dict: Nómina calculada
        """
        # Devengado
        salario_base = self.empleado.salario_base
        auxilio_transporte = self._calcular_auxilio_transporte(salario_base)
        horas_extras = Decimal(str(kwargs.get('horas_extras', 0)))
        bonificaciones = Decimal(str(kwargs.get('bonificaciones', 0)))
        comisiones = Decimal(str(kwargs.get('comisiones', 0)))
        
        total_devengado = (
            salario_base +
            auxilio_transporte +
            horas_extras +
            bonificaciones +
            comisiones
        )
        
        # Deducciones empleado (sobre salario base)
        base_calculo = salario_base
        salud = base_calculo * self.PORCENTAJE_SALUD_EMPLEADO
        pension = base_calculo * self.PORCENTAJE_PENSION_EMPLEADO
        prestamos = Decimal(str(kwargs.get('prestamos', 0)))
        otras_deducciones = Decimal(str(kwargs.get('otras_deducciones', 0)))
        
        total_deducciones = (
            salud +
            pension +
            prestamos +
            otras_deducciones
        )
        
        # Neto a pagar
        neto_pagar = total_devengado - total_deducciones
        
        # Aportes patronales (empresa)
        salud_empresa = base_calculo * self.PORCENTAJE_SALUD_EMPRESA
        pension_empresa = base_calculo * self.PORCENTAJE_PENSION_EMPRESA
        arl = base_calculo * self.PORCENTAJE_ARL
        caja_compensacion = base_calculo * self.PORCENTAJE_CAJA
        icbf = base_calculo * self.PORCENTAJE_ICBF
        sena = base_calculo * self.PORCENTAJE_SENA
        
        total_aportes_empresa = (
            salud_empresa +
            pension_empresa +
            arl +
            caja_compensacion +
            icbf +
            sena
        )
        
        # Costo total para la empresa
        costo_total_empresa = (
            salario_base +
            auxilio_transporte +
            horas_extras +
            bonificaciones +
            comisiones +
            total_aportes_empresa
        )
        
        return {
            # Devengado
            'salario_base': salario_base,
            'auxilio_transporte': auxilio_transporte,
            'horas_extras': horas_extras,
            'bonificaciones': bonificaciones,
            'comisiones': comisiones,
            'total_devengado': total_devengado,
            
            # Deducciones
            'salud': salud,
            'pension': pension,
            'prestamos': prestamos,
            'otras_deducciones': otras_deducciones,
            'total_deducciones': total_deducciones,
            
            # Neto
            'neto_pagar': neto_pagar,
            
            # Aportes empresa
            'salud_empresa': salud_empresa,
            'pension_empresa': pension_empresa,
            'arl': arl,
            'caja_compensacion': caja_compensacion,
            'icbf': icbf,
            'sena': sena,
            'total_aportes_empresa': total_aportes_empresa,
            
            # Costo total
            'costo_total_empresa': costo_total_empresa,
            
            # Meta
            'mes': mes,
            'anio': anio,
        }
    
    def _calcular_auxilio_transporte(self, salario_base):
        """
        Calcula auxilio de transporte
        Solo aplica si gana <= 2 SMMLV
        """
        if salario_base <= (self.SALARIO_MINIMO * 2):
            return self.AUXILIO_TRANSPORTE
        return Decimal('0')
    
    def calcular_horas_extras(self, horas, tipo='ordinarias_diurnas'):
        """
        Calcula valor de horas extras
        
        Tipos:
        - ordinarias_diurnas: 25% recargo
        - ordinarias_nocturnas: 75% recargo
        - dominicales_festivas: 75% recargo
        - dominicales_festivas_nocturnas: 110% recargo
        """
        valor_hora = self.empleado.salario_base / Decimal('240')  # 240 horas/mes
        
        recargos = {
            'ordinarias_diurnas': Decimal('1.25'),  # 25%
            'ordinarias_nocturnas': Decimal('1.75'),  # 75%
            'dominicales_festivas': Decimal('1.75'),  # 75%
            'dominicales_festivas_nocturnas': Decimal('2.10'),  # 110%
        }
        
        recargo = recargos.get(tipo, Decimal('1.25'))
        return valor_hora * Decimal(str(horas)) * recargo
    
    def calcular_liquidacion(self, fecha_retiro=None):
        """
        Calcula liquidación al retiro
        
        Returns:
            dict: Liquidación completa
        """
        if not fecha_retiro:
            fecha_retiro = timezone.now().date()
        
        fecha_ingreso = self.empleado.fecha_ingreso
        
        # Tiempo trabajado
        dias_trabajados = (fecha_retiro - fecha_ingreso).days
        anos_trabajados = dias_trabajados / Decimal('360')  # Año comercial
        
        salario_base = self.empleado.salario_base
        
        # Prima de servicios (15 días por semestre)
        dias_semestre = (dias_trabajados % 180)
        prima_servicios = (salario_base / Decimal('360')) * Decimal(str(dias_semestre))
        
        # Cesantías (1 mes por año)
        cesantias = (salario_base * Decimal(str(dias_trabajados))) / Decimal('360')
        
        # Intereses sobre cesantías (12% anual)
        intereses_cesantias = cesantias * Decimal('0.12') * (Decimal(str(dias_trabajados)) / Decimal('360'))
        
        # Vacaciones (15 días hábiles por año)
        dias_vacaciones = (dias_trabajados / Decimal('360')) * Decimal('15')
        vacaciones = (salario_base / Decimal('30')) * dias_vacaciones
        
        total_liquidacion = (
            prima_servicios +
            cesantias +
            intereses_cesantias +
            vacaciones
        )
        
        return {
            'dias_trabajados': int(dias_trabajados),
            'anos_trabajados': float(anos_trabajados),
            'prima_servicios': prima_servicios,
            'cesantias': cesantias,
            'intereses_cesantias': intereses_cesantias,
            'vacaciones': vacaciones,
            'total_liquidacion': total_liquidacion,
            'fecha_ingreso': fecha_ingreso,
            'fecha_retiro': fecha_retiro,
        }
    
    def calcular_prestaciones_sociales_mes(self):
        """
        Calcula el valor mensual de prestaciones sociales
        (provisión que debe hacer la empresa)
        """
        salario_base = self.empleado.salario_base
        
        # Cesantías: 8.33% (1 mes / 12)
        cesantias = salario_base * Decimal('0.0833')
        
        # Intereses cesantías: 1% (12% anual / 12)
        intereses = salario_base * Decimal('0.01')
        
        # Prima: 8.33% (1 mes / 12)
        prima = salario_base * Decimal('0.0833')
        
        # Vacaciones: 4.17% (15 días / 360 * 12)
        vacaciones = salario_base * Decimal('0.0417')
        
        total_prestaciones = cesantias + intereses + prima + vacaciones
        
        return {
            'cesantias': cesantias,
            'intereses_cesantias': intereses,
            'prima_servicios': prima,
            'vacaciones': vacaciones,
            'total_prestaciones': total_prestaciones,
        }
    
    @staticmethod
    def generar_nomina_masiva(empleados, mes, anio):
        """
        Genera nómina para múltiples empleados
        
        Args:
            empleados: QuerySet de empleados
            mes: Mes a generar
            anio: Año
            
        Returns:
            list: Lista de nóminas generadas
        """
        from finanzas.models import Nomina
        
        nominas = []
        
        for empleado in empleados:
            # Verificar si ya existe
            existe = Nomina.objects.filter(
                empleado=empleado,
                mes=mes,
                anio=anio
            ).exists()
            
            if existe:
                continue
            
            # Calcular
            calculadora = CalculadoraNomina(empleado)
            datos = calculadora.calcular_nomina_mes(mes, anio)
            
            # Crear nómina
            nomina = Nomina.objects.create(
                empleado=empleado,
                mes=mes,
                anio=anio,
                salario_base=datos['salario_base'],
                auxilio_transporte=datos['auxilio_transporte'],
                horas_extras=datos['horas_extras'],
                bonificaciones=datos['bonificaciones'],
                comisiones=datos['comisiones'],
                total_devengado=datos['total_devengado'],
                salud=datos['salud'],
                pension=datos['pension'],
                prestamos=datos['prestamos'],
                otras_deducciones=datos['otras_deducciones'],
                total_deducciones=datos['total_deducciones'],
                neto_pagar=datos['neto_pagar'],
                salud_empresa=datos['salud_empresa'],
                pension_empresa=datos['pension_empresa'],
                arl=datos['arl'],
                caja_compensacion=datos['caja_compensacion'],
                icbf=datos['icbf'],
                sena=datos['sena'],
                total_aportes_empresa=datos['total_aportes_empresa'],
                costo_total_empresa=datos['costo_total_empresa'],
            )
            
            nominas.append(nomina)
        
        return nominas