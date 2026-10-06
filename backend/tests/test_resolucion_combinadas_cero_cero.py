"""La ruta legacy de combinadas no resuelve selecciones sobre NBA 0–0."""

from unittest.mock import MagicMock, patch

from motor.resolucion_combinadas import resolver_combinadas


def test_seleccion_cero_cero_permanece_pendiente_sin_escrituras():
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        ("seleccion", "combinada", "partido", "COMPLETO", "OVER", 210.5,
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None),
    ]
    conexion = MagicMock()
    conexion.cursor.return_value.__enter__.return_value = cursor
    pool = MagicMock()
    pool.connection.return_value.__enter__.return_value = conexion

    with patch("motor.resolucion_combinadas.obtener_pool", return_value=pool), \
         patch("motor.resolucion_combinadas._calcular_valor_real") as calcular, \
         patch("motor.resolucion_combinadas._actualizar_estado_combinada") as actualizar:
        resultado = resolver_combinadas()

    assert resultado["selecciones_pendientes"] == 1
    assert resultado["selecciones_resueltas"] == 0
    assert resultado["errores"] == 0
    assert cursor.execute.call_count == 1  # solo SELECT, ningún UPDATE
    calcular.assert_not_called()
    actualizar.assert_not_called()
