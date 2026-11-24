"""Pruebas end-to-end con Playwright contra la app levantada (docker compose up).

Correr con:  python -m pytest tests_e2e --base-url http://localhost:8000
"""

import uuid

from playwright.sync_api import Page, expect


def etiqueta_unica(prefijo: str) -> str:
    # La app guarda el historial entre pruebas; una etiqueta única evita confundir registros.
    return f"{prefijo}-{uuid.uuid4().hex[:6]}"


def convertir(page: Page, valor: str, de: str, a: str, etiqueta: str = "") -> None:
    page.goto("/")
    page.get_by_label("Valor").fill(valor)
    page.get_by_label("De", exact=True).select_option(de)
    page.get_by_label("A", exact=True).select_option(a)
    page.get_by_label("Etiqueta (opcional)").fill(etiqueta)
    page.get_by_role("button", name="Convertir").click()


def test_convierte_y_muestra_el_resultado(page: Page):
    convertir(page, "100", "C", "F")
    expect(page.get_by_role("status")).to_have_text("100 °C = 212 °F")


def test_la_conversion_aparece_en_el_historial(page: Page):
    etiqueta = etiqueta_unica("horno")
    convertir(page, "0", "C", "K", etiqueta)
    expect(page.locator("#historial li").first).to_contain_text(etiqueta)
    expect(page.locator("#historial li").first).to_contain_text("0 °C = 273.15 K")


def test_por_debajo_del_cero_absoluto_muestra_error(page: Page):
    convertir(page, "-500", "C", "F")
    expect(page.get_by_role("status")).to_contain_text("cero absoluto")


def test_regresion_xss_capa_servidor_rechaza_la_etiqueta(page: Page):
    # Capa 1 de la defensa: el servidor no acepta HTML en la etiqueta.
    marca = uuid.uuid4().hex[:6]
    convertir(page, "1", "C", "C", f'<img src=x id="xss-{marca}">')

    expect(page.get_by_role("status")).to_contain_text("letras, números")
    expect(page.locator(f"#xss-{marca}")).to_have_count(0)


def test_regresion_xss_capa_frontend_muestra_la_etiqueta_como_texto(page: Page):
    # Capa 2 de la defensa: aunque el servidor dejara pasar HTML, el frontend no lo interpreta.
    # Simulamos esa respuesta del servidor interceptando la petición con page.route.
    marca = uuid.uuid4().hex[:6]
    etiqueta = f'<img src=x id="xss-{marca}">'
    falsa = [
        {
            "id": 1,
            "valor": 1,
            "de": "C",
            "a": "C",
            "resultado": 1,
            "etiqueta": etiqueta,
            "fecha": "2026-01-01T00:00:00Z",
        }
    ]
    page.route("**/conversiones?limite=10", lambda ruta: ruta.fulfill(json=falsa))
    page.goto("/")

    primero = page.locator("#historial li").first
    expect(primero).to_contain_text(etiqueta)  # se ve el texto literal
    expect(page.locator(f"#xss-{marca}")).to_have_count(0)  # y no existe como elemento
