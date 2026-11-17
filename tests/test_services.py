"""Pruebas unitarias de la lógica de negocio (sin HTTP)."""

import pytest

from app import services


@pytest.mark.parametrize(
    ("valor", "de", "a", "esperado"),
    [
        (0, "C", "F", 32.0),
        (100, "C", "F", 212.0),
        (32, "F", "C", 0.0),
        (0, "K", "C", -273.15),
        (-40, "C", "F", -40.0),  # el único punto donde °C y °F coinciden
        (25, "C", "C", 25.0),
    ],
)
def test_conversiones_conocidas(valor, de, a, esperado):
    assert services.convertir(valor, de, a) == esperado


def test_ida_y_vuelta_regresa_al_valor_original():
    f = services.convertir(37, "C", "F", decimales=6)
    assert services.convertir(f, "F", "C", decimales=6) == 37.0


@pytest.mark.parametrize(("valor", "escala"), [(-273.16, "C"), (-459.68, "F"), (-0.01, "K")])
def test_por_debajo_del_cero_absoluto_se_rechaza(valor, escala):
    with pytest.raises(services.TemperaturaInvalidaError):
        services.convertir(valor, escala, "C")


@pytest.mark.parametrize(("valor", "escala"), [(-273.15, "C"), (-459.67, "F"), (0, "K")])
def test_el_cero_absoluto_exacto_si_se_permite(valor, escala):
    services.convertir(valor, escala, "K")


def test_redondeo_respeta_decimales():
    assert services.convertir(1, "C", "F", decimales=0) == 34.0
    assert services.convertir(1, "C", "F", decimales=1) == 33.8


def test_no_devuelve_cero_negativo():
    resultado = services.convertir(-0.001, "C", "C", decimales=2)
    assert str(resultado) == "0.0"
