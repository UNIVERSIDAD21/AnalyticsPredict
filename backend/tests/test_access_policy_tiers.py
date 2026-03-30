# -*- coding: utf-8 -*-

from servicios.access_policy import (
    evaluar_capability,
    capability_habilitada,
    tipo_gate,
    TipoGate,
)


def test_visitante_habilita_capas_publicas_y_bloquea_base():
    assert capability_habilitada("public.shell", "INVITADO") is True
    assert capability_habilitada("public.center", "INVITADO") is True
    assert capability_habilitada("analisis.nba.base", "INVITADO") is False
    assert tipo_gate("analisis.nba.base", "INVITADO") == TipoGate.BASE_REQUIRED


def test_base_habilita_flujo_operativo_y_bloquea_depth_premium():
    assert capability_habilitada("analisis.nba.base", "BASE") is True
    assert capability_habilitada("futbol.base", "BASE") is True
    assert capability_habilitada("premium.depth", "BASE") is False
    assert tipo_gate("premium.depth", "BASE") == TipoGate.PREMIUM_REQUIRED


def test_premium_habilita_depth():
    assert capability_habilitada("premium.depth", "PREMIUM") is True
    assert tipo_gate("premium.depth", "PREMIUM") is None


def test_chat_contextual_permanece_fuera_de_alcance():
    assert capability_habilitada("chat.contextual", "INVITADO") is False
    assert capability_habilitada("chat.contextual", "BASE") is False
    assert capability_habilitada("chat.contextual", "PREMIUM") is False
    assert tipo_gate("chat.contextual", "BASE") == TipoGate.DISABLED


def test_evaluar_capability_retorna_payload_consistente():
    resultado = evaluar_capability("bitacora.personal", "INVITADO")
    assert resultado.capability == "bitacora.personal"
    assert resultado.tier_actual == "INVITADO"
    assert resultado.tier_requerido == "BASE"
    assert resultado.enabled is False
    assert resultado.gate == TipoGate.BASE_REQUIRED
