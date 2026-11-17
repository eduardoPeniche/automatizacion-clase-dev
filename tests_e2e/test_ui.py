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


def test_regresion_xss_la_etiqueta_se_muestra_como_texto(page: Page):
    # Regresión del XSS de la Unidad II: la etiqueta nunca debe interpretarse como HTML.
    marca = uuid.uuid4().hex[:6]
    etiqueta = f'<img src=x id="xss-{marca}">'
    convertir(page, "1", "C", "C", etiqueta)

    primero = page.locator("#historial li").first
    expect(primero).to_contain_text(etiqueta)  # se ve el texto literal
    expect(page.locator(f"#xss-{marca}")).to_have_count(0)  # y no existe como elemento
