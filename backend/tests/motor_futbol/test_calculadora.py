# -*- coding: utf-8 -*-
"""
test_calculadora.py — Tests unitarios para CalculadoraProbabilidad.

Tests obligatorios según especificación:
- test_prob_over_distribucion_estandar
- test_prob_over_under_suman_uno
- test_intervalo_confianza_90
- test_valor_esperado_calculo
"""

import pytest
import math

from motor_futbol.prediccion.calculadora_probabilidad import CalculadoraProbabilidad


class TestCDFNormal:
    """Tests para la función de distribución acumulativa normal."""

    def test_cdf_normal_cero(self):
        """CDF(0) = 0.5 para distribución estándar."""
        resultado = CalculadoraProbabilidad.cdf_normal(0)
        assert abs(resultado - 0.5) < 0.001

    def test_cdf_normal_positivo(self):
        """CDF de valores positivos > 0.5."""
        resultado = CalculadoraProbabilidad.cdf_normal(1.0)
        # CDF(1) ≈ 0.8413
        assert resultado > 0.5
        assert abs(resultado - 0.8413) < 0.01

    def test_cdf_normal_negativo(self):
        """CDF de valores negativos < 0.5."""
        resultado = CalculadoraProbabilidad.cdf_normal(-1.0)
        # CDF(-1) ≈ 0.1587
        assert resultado < 0.5
        assert abs(resultado - 0.1587) < 0.01

    def test_cdf_normal_extremos(self):
        """CDF para valores extremos."""
        assert CalculadoraProbabilidad.cdf_normal(-4) < 0.01
        assert CalculadoraProbabilidad.cdf_normal(4) > 0.99


class TestProbOver:
    """Tests para cálculo de probabilidad over."""

    def test_prob_over_distribucion_estandar(self):
        """
        Test prob_over con distribución estándar (μ=10, σ=2).

        Para línea=10 (igual a la media):
        P(X > 10) = 1 - Φ((10-10)/2) = 1 - Φ(0) = 1 - 0.5 = 0.5
        """
        media = 10.0
        std = 2.0
        linea = 10.0

        probabilidad = CalculadoraProbabilidad.prob_over(media, std, linea)
        assert abs(probabilidad - 0.5) < 0.001

    def test_prob_over_linea_baja(self):
        """
        Cuando la línea está debajo de la media, prob_over > 0.5.

        Para μ=10, σ=2, línea=8:
        P(X > 8) = 1 - Φ((8-10)/2) = 1 - Φ(-1) ≈ 0.84
        """
        probabilidad = CalculadoraProbabilidad.prob_over(10.0, 2.0, 8.0)
        assert probabilidad > 0.5
        assert abs(probabilidad - 0.8413) < 0.01

    def test_prob_over_linea_alta(self):
        """
        Cuando la línea está arriba de la media, prob_over < 0.5.

        Para μ=10, σ=2, línea=12:
        P(X > 12) = 1 - Φ((12-10)/2) = 1 - Φ(1) ≈ 0.16
        """
        probabilidad = CalculadoraProbabilidad.prob_over(10.0, 2.0, 12.0)
        assert probabilidad < 0.5
        assert abs(probabilidad - 0.1587) < 0.01

    def test_prob_over_std_muy_pequena(self):
        """Con std muy pequeña, prob_over es casi 0 o 1."""
        # Media muy por encima de línea
        prob = CalculadoraProbabilidad.prob_over(10.0, 0.1, 8.0)
        assert prob > 0.99

        # Media muy por debajo de línea
        prob = CalculadoraProbabilidad.prob_over(8.0, 0.1, 10.0)
        assert prob < 0.01

    def test_prob_over_std_cero_manejada(self):
        """Std cero no causa división por cero."""
        # No debe lanzar excepción
        prob = CalculadoraProbabilidad.prob_over(10.0, 0.0, 10.0)
        assert 0 <= prob <= 1


class TestProbUnder:
    """Tests para cálculo de probabilidad under."""

    def test_prob_under_media_igual_linea(self):
        """Prob under = 0.5 cuando media = línea."""
        probabilidad = CalculadoraProbabilidad.prob_under(10.0, 2.0, 10.0)
        assert abs(probabilidad - 0.5) < 0.001

    def test_prob_under_linea_alta(self):
        """Prob under alta cuando línea > media."""
        probabilidad = CalculadoraProbabilidad.prob_under(10.0, 2.0, 12.0)
        assert probabilidad > 0.5
        assert abs(probabilidad - 0.8413) < 0.01


class TestProbOverUnderSumanUno:
    """Tests que verifican que over + under = 1."""

    def test_prob_over_under_suman_uno(self):
        """P(over) + P(under) = 1 para cualquier combinación."""
        casos = [
            (10.0, 2.0, 10.0),   # Media = línea
            (10.0, 2.0, 8.5),    # Línea < media
            (10.0, 2.0, 11.5),   # Línea > media
            (5.5, 1.0, 6.0),     # Otros valores
            (15.0, 3.0, 14.5),
        ]

        for media, std, linea in casos:
            prob_over = CalculadoraProbabilidad.prob_over(media, std, linea)
            prob_under = CalculadoraProbabilidad.prob_under(media, std, linea)
            suma = prob_over + prob_under

            assert abs(suma - 1.0) < 0.001, (
                f"over({prob_over:.4f}) + under({prob_under:.4f}) = {suma:.4f} != 1.0 "
                f"para μ={media}, σ={std}, línea={linea}"
            )

    def test_prob_over_under_extremos(self):
        """Verificar suma = 1 incluso en extremos."""
        # Línea muy por debajo
        prob_over = CalculadoraProbabilidad.prob_over(10.0, 2.0, 4.0)
        prob_under = CalculadoraProbabilidad.prob_under(10.0, 2.0, 4.0)
        assert abs(prob_over + prob_under - 1.0) < 0.001

        # Línea muy por arriba
        prob_over = CalculadoraProbabilidad.prob_over(10.0, 2.0, 16.0)
        prob_under = CalculadoraProbabilidad.prob_under(10.0, 2.0, 16.0)
        assert abs(prob_over + prob_under - 1.0) < 0.001


class TestIntervaloConfianza:
    """Tests para intervalos de confianza."""

    def test_intervalo_confianza_90(self):
        """
        Intervalo de confianza 90% usa z=1.645.

        Para μ=10, σ=2:
        IC_90 = [10 - 1.645*2, 10 + 1.645*2] = [6.71, 13.29]
        """
        media = 10.0
        std = 2.0

        inferior, superior = CalculadoraProbabilidad.intervalo_confianza(media, std, 0.90)

        assert abs(inferior - 6.71) < 0.01
        assert abs(superior - 13.29) < 0.01

    def test_intervalo_confianza_95(self):
        """Intervalo de confianza 95% usa z=1.96."""
        inferior, superior = CalculadoraProbabilidad.intervalo_confianza(10.0, 2.0, 0.95)

        # IC_95 = [10 - 1.96*2, 10 + 1.96*2] = [6.08, 13.92]
        assert abs(inferior - 6.08) < 0.01
        assert abs(superior - 13.92) < 0.01

    def test_intervalo_confianza_simetrico(self):
        """El intervalo es simétrico alrededor de la media."""
        media = 10.0
        std = 2.0
        inferior, superior = CalculadoraProbabilidad.intervalo_confianza(media, std, 0.90)

        distancia_inferior = media - inferior
        distancia_superior = superior - media

        assert abs(distancia_inferior - distancia_superior) < 0.001

    def test_intervalo_confianza_mayor_nivel_mas_ancho(self):
        """Mayor nivel de confianza implica intervalo más ancho."""
        media = 10.0
        std = 2.0

        ic_80 = CalculadoraProbabilidad.intervalo_confianza(media, std, 0.80)
        ic_90 = CalculadoraProbabilidad.intervalo_confianza(media, std, 0.90)
        ic_95 = CalculadoraProbabilidad.intervalo_confianza(media, std, 0.95)

        ancho_80 = ic_80[1] - ic_80[0]
        ancho_90 = ic_90[1] - ic_90[0]
        ancho_95 = ic_95[1] - ic_95[0]

        assert ancho_80 < ancho_90 < ancho_95


class TestProbabilidadesLineas:
    """Tests para cálculo de probabilidades en múltiples líneas."""

    def test_probabilidades_lineas_formato(self):
        """Verifica formato de salida."""
        lineas = [8.5, 9.5, 10.5]
        resultado = CalculadoraProbabilidad.probabilidades_lineas(10.0, 2.0, lineas)

        assert "over_8.5" in resultado
        assert "under_8.5" in resultado
        assert "over_9.5" in resultado
        assert "under_9.5" in resultado
        assert "over_10.5" in resultado
        assert "under_10.5" in resultado

    def test_probabilidades_lineas_valores_coherentes(self):
        """Probabilidades over decrecen con líneas mayores."""
        lineas = [8.5, 9.5, 10.5, 11.5]
        resultado = CalculadoraProbabilidad.probabilidades_lineas(10.0, 2.0, lineas)

        prob_over_8_5 = resultado["over_8.5"]
        prob_over_9_5 = resultado["over_9.5"]
        prob_over_10_5 = resultado["over_10.5"]
        prob_over_11_5 = resultado["over_11.5"]

        assert prob_over_8_5 > prob_over_9_5 > prob_over_10_5 > prob_over_11_5


class TestValorEsperado:
    """Tests para cálculo de valor esperado."""

    def test_valor_esperado_calculo(self):
        """
        Test valor esperado básico.

        EV = (prob × cuota) - 1

        Con prob=0.6, cuota=2.0:
        EV = (0.6 × 2.0) - 1 = 0.2 = +20%
        """
        probabilidad = 0.6
        cuota = 2.0

        ev = CalculadoraProbabilidad.valor_esperado(probabilidad, cuota)
        assert abs(ev - 0.2) < 0.001

    def test_valor_esperado_negativo(self):
        """EV negativo cuando probabilidad baja."""
        # Con prob=0.4, cuota=2.0: EV = 0.4*2 - 1 = -0.2
        ev = CalculadoraProbabilidad.valor_esperado(0.4, 2.0)
        assert ev < 0
        assert abs(ev - (-0.2)) < 0.001

    def test_valor_esperado_cero(self):
        """EV cero cuando cuota justa."""
        # Prob=0.5, cuota=2.0: EV = 0.5*2 - 1 = 0
        ev = CalculadoraProbabilidad.valor_esperado(0.5, 2.0)
        assert abs(ev) < 0.001


class TestEdge:
    """Tests para cálculo de edge."""

    def test_edge_positivo(self):
        """Edge positivo cuando modelo más confiado que mercado."""
        # Prob modelo = 0.6, cuota = 2.0 → prob implícita = 0.5
        # Edge = 0.6 - 0.5 = 0.1
        edge = CalculadoraProbabilidad.edge(0.6, 2.0)
        assert abs(edge - 0.1) < 0.001

    def test_edge_negativo(self):
        """Edge negativo cuando mercado más confiado."""
        # Prob modelo = 0.4, cuota = 2.0 → prob implícita = 0.5
        # Edge = 0.4 - 0.5 = -0.1
        edge = CalculadoraProbabilidad.edge(0.4, 2.0)
        assert abs(edge - (-0.1)) < 0.001


class TestKellyCriterion:
    """Tests para criterio de Kelly."""

    def test_kelly_criterion_basico(self):
        """
        Test Kelly básico.

        f* = (p*(b) - q) / b
        donde b = cuota - 1

        Con p=0.6, cuota=2.0 (b=1):
        f* = (0.6*1 - 0.4) / 1 = 0.2
        Quarter Kelly = 0.2 * 0.25 = 0.05
        """
        kelly = CalculadoraProbabilidad.kelly_criterion(0.6, 2.0, fraccion=0.25)
        assert abs(kelly - 0.05) < 0.001

    def test_kelly_criterion_sin_edge(self):
        """Kelly = 0 cuando no hay edge."""
        # Prob = 0.5, cuota = 2.0 → f* = (0.5*1 - 0.5)/1 = 0
        kelly = CalculadoraProbabilidad.kelly_criterion(0.5, 2.0)
        assert kelly == 0.0

    def test_kelly_criterion_edge_negativo(self):
        """Kelly = 0 cuando edge negativo."""
        kelly = CalculadoraProbabilidad.kelly_criterion(0.4, 2.0)
        assert kelly == 0.0

    def test_kelly_criterion_cuota_invalida(self):
        """Kelly = 0 con cuota inválida."""
        assert CalculadoraProbabilidad.kelly_criterion(0.6, 1.0) == 0.0
        assert CalculadoraProbabilidad.kelly_criterion(0.6, 0.0) == 0.0

    def test_kelly_criterion_prob_invalida(self):
        """Kelly = 0 con probabilidad inválida."""
        assert CalculadoraProbabilidad.kelly_criterion(0.0, 2.0) == 0.0
        assert CalculadoraProbabilidad.kelly_criterion(1.0, 2.0) == 0.0
        assert CalculadoraProbabilidad.kelly_criterion(-0.1, 2.0) == 0.0


class TestCuotaJusta:
    """Tests para cálculo de cuota justa."""

    def test_cuota_justa_50_porciento(self):
        """Cuota justa para 50% = 2.0."""
        cuota = CalculadoraProbabilidad.cuota_justa(0.5)
        assert abs(cuota - 2.0) < 0.001

    def test_cuota_justa_25_porciento(self):
        """Cuota justa para 25% = 4.0."""
        cuota = CalculadoraProbabilidad.cuota_justa(0.25)
        assert abs(cuota - 4.0) < 0.001

    def test_cuota_justa_extremos(self):
        """Cuotas para probabilidades extremas."""
        assert CalculadoraProbabilidad.cuota_justa(0.0) == float("inf")
        assert CalculadoraProbabilidad.cuota_justa(1.0) == 1.0


class TestProbabilidadImplicita:
    """Tests para probabilidad implícita."""

    def test_probabilidad_implicita_cuota_2(self):
        """Prob implícita de cuota 2.0 = 50%."""
        prob = CalculadoraProbabilidad.probabilidad_implicita(2.0)
        assert abs(prob - 0.5) < 0.001

    def test_probabilidad_implicita_cuota_4(self):
        """Prob implícita de cuota 4.0 = 25%."""
        prob = CalculadoraProbabilidad.probabilidad_implicita(4.0)
        assert abs(prob - 0.25) < 0.001


class TestOverround:
    """Tests para cálculo de overround."""

    def test_overround_mercado_justo(self):
        """Overround = 1.0 para mercado sin vig."""
        overround = CalculadoraProbabilidad.calcular_overround(2.0, 2.0)
        assert abs(overround - 1.0) < 0.001

    def test_overround_mercado_con_vig(self):
        """Overround > 1.0 indica margen de la casa."""
        # Cuotas típicas: 1.90/1.90 → OR = 0.526 + 0.526 = 1.052
        overround = CalculadoraProbabilidad.calcular_overround(1.90, 1.90)
        assert overround > 1.0
        assert abs(overround - 1.0526) < 0.01


class TestCuotasJustas:
    """Tests para eliminación de vig."""

    def test_cuotas_justas_elimina_vig(self):
        """Cuotas justas eliminan el margen."""
        cuota_over = 1.90
        cuota_under = 1.90

        justa_over, justa_under = CalculadoraProbabilidad.cuotas_justas(
            cuota_over, cuota_under
        )

        # Deberían ser ≈ 2.0 cada una
        assert justa_over > cuota_over
        assert justa_under > cuota_under
        assert abs(justa_over - 2.0) < 0.05
        assert abs(justa_under - 2.0) < 0.05

    def test_cuotas_justas_suman_100(self):
        """Probabilidades justas suman 100%."""
        justa_over, justa_under = CalculadoraProbabilidad.cuotas_justas(1.85, 1.95)

        prob_over = 1.0 / justa_over
        prob_under = 1.0 / justa_under

        assert abs(prob_over + prob_under - 1.0) < 0.001


class TestDistanciaZ:
    """Tests para cálculo de distancia z."""

    def test_distancia_z_una_std(self):
        """Distancia de 1 std."""
        distancia = CalculadoraProbabilidad.distancia_z(10.0, 2.0, 12.0)
        assert abs(distancia - 1.0) < 0.001

    def test_distancia_z_dos_std(self):
        """Distancia de 2 std."""
        distancia = CalculadoraProbabilidad.distancia_z(10.0, 2.0, 14.0)
        assert abs(distancia - 2.0) < 0.001

    def test_distancia_z_siempre_positiva(self):
        """Distancia z siempre positiva (valor absoluto)."""
        distancia_arriba = CalculadoraProbabilidad.distancia_z(10.0, 2.0, 12.0)
        distancia_abajo = CalculadoraProbabilidad.distancia_z(10.0, 2.0, 8.0)

        assert distancia_arriba > 0
        assert distancia_abajo > 0
        assert abs(distancia_arriba - distancia_abajo) < 0.001


class TestPercentil:
    """Tests para cálculo de percentiles."""

    def test_percentil_media(self):
        """La media está en el percentil 50."""
        percentil = CalculadoraProbabilidad.percentil(10.0, 2.0, 10.0)
        assert abs(percentil - 0.5) < 0.001

    def test_percentil_una_std_arriba(self):
        """Una std arriba ≈ percentil 84."""
        percentil = CalculadoraProbabilidad.percentil(10.0, 2.0, 12.0)
        assert abs(percentil - 0.8413) < 0.01

    def test_percentil_una_std_abajo(self):
        """Una std abajo ≈ percentil 16."""
        percentil = CalculadoraProbabilidad.percentil(10.0, 2.0, 8.0)
        assert abs(percentil - 0.1587) < 0.01
