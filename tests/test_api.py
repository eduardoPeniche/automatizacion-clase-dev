"""Pruebas de integración de la API con TestClient (sin levantar el servidor)."""

import pytest
from fastapi.testclient import TestClient

from app import repository
from app.main import app
from app.models import MAX_LOTE

client = TestClient(app)


@pytest.fixture(autouse=True)
def historial_vacio():
    repository.limpiar()
    yield
    repository.limpiar()


def test_salud():
    respuesta = client.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_crear_conversion_y_verla_en_el_historial():
    respuesta = client.post("/conversiones", json={"valor": 100, "de": "C", "a": "F", "etiqueta": "agua"})
    assert respuesta.status_code == 201
    assert respuesta.json()["resultado"] == 212.0

    historial = client.get("/conversiones").json()
    assert historial[0]["etiqueta"] == "agua"
    assert historial[0]["resultado"] == 212.0


def test_el_historial_muestra_primero_lo_mas_reciente():
    for valor in (1, 2, 3):
        client.post("/conversiones", json={"valor": valor, "de": "C", "a": "C"})
    valores = [c["valor"] for c in client.get("/conversiones").json()]
    assert valores == [3, 2, 1]


def test_el_historial_no_crece_sin_limite():
    for valor in range(repository.MAX_HISTORIAL + 5):
        client.post("/conversiones", json={"valor": valor, "de": "C", "a": "C"})
    historial = client.get("/conversiones", params={"limite": repository.MAX_HISTORIAL}).json()
    assert len(historial) == repository.MAX_HISTORIAL


def test_por_debajo_del_cero_absoluto_responde_422_y_no_se_guarda():
    respuesta = client.post("/conversiones", json={"valor": -300, "de": "C", "a": "F"})
    assert respuesta.status_code == 422
    assert "cero absoluto" in respuesta.json()["detail"]
    assert client.get("/conversiones").json() == []


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"valor": 10, "de": "X", "a": "F"},  # escala inexistente
        {"valor": 10, "de": "C", "a": "F", "decimales": 7},  # demasiados decimales
        {"valor": 10, "de": "C", "a": "F", "etiqueta": "a" * 41},  # etiqueta demasiado larga
        {"valor": 10_000_000, "de": "C", "a": "F"},  # fuera de rango
        {"de": "C", "a": "F"},  # falta el valor
    ],
)
def test_entradas_invalidas_responden_422(cuerpo):
    assert client.post("/conversiones", json=cuerpo).status_code == 422


def test_nan_se_rechaza():
    # Regresión de la Unidad II: un NaN guardado rompía el listado completo.
    respuesta = client.post(
        "/conversiones",
        content='{"valor": NaN, "de": "C", "a": "F"}',
        headers={"Content-Type": "application/json"},
    )
    assert respuesta.status_code == 422
    assert client.get("/conversiones").status_code == 200


def test_la_api_devuelve_la_etiqueta_tal_cual():
    # El backend guarda texto; escaparlo al mostrarlo es responsabilidad del frontend.
    etiqueta = "<b>hola</b>"
    client.post("/conversiones", json={"valor": 1, "de": "C", "a": "C", "etiqueta": etiqueta})
    assert client.get("/conversiones").json()[0]["etiqueta"] == etiqueta


def test_lote_convierte_todos_los_valores():
    respuesta = client.post("/conversiones/lote", json={"valores": [0, 100, -40], "de": "C", "a": "F"})
    assert respuesta.status_code == 200
    assert respuesta.json()["resultados"] == [32.0, 212.0, -40.0]


def test_lote_en_el_limite_se_acepta():
    respuesta = client.post("/conversiones/lote", json={"valores": [1.0] * MAX_LOTE, "de": "C", "a": "F"})
    assert respuesta.status_code == 200


def test_lote_por_encima_del_limite_se_rechaza():
    # Sin este límite, una sola petición con millones de valores bloquea el servicio.
    respuesta = client.post("/conversiones/lote", json={"valores": [1.0] * (MAX_LOTE + 1), "de": "C", "a": "F"})
    assert respuesta.status_code == 422


def test_lote_vacio_se_rechaza():
    assert client.post("/conversiones/lote", json={"valores": [], "de": "C", "a": "F"}).status_code == 422


def test_cabeceras_de_seguridad_presentes():
    cabeceras = client.get("/").headers
    assert cabeceras["Content-Security-Policy"].startswith("default-src 'self'")
    assert cabeceras["X-Content-Type-Options"] == "nosniff"
    assert cabeceras["X-Frame-Options"] == "DENY"
