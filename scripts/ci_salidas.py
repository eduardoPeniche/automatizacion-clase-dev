"""Extrae datos pequeños de los reportes de cada etapa para armar resumen.json.

Solo usa la biblioteca estándar: corre en el runner sin instalar nada.

Uso:
  ruff check . --output-format=json --exit-zero | python3 scripts/ci_salidas.py contar
  python3 scripts/ci_salidas.py fallidas reports/pytest.xml
  python3 scripts/ci_salidas.py zap reports/zap/zap-reporte.json .zap/rules.tsv

Cada comando imprime una sola línea (un número o un JSON compacto) para $GITHUB_OUTPUT.
"""

import json
import sys
import xml.etree.ElementTree as ET  # noqa: S405  (el XML lo genera nuestro propio pytest, no un tercero)
from pathlib import Path

MAX_ELEMENTOS = 20
MAX_TEXTO = 200


def limpiar(texto: object) -> str:
    """Quita saltos de línea y caracteres de control, y recorta.

    Estos textos los leerá un agente de IA: un nombre de prueba con saltos de línea
    o instrucciones largas es un intento de prompt injection.
    """
    return "".join(c if c.isprintable() else " " for c in str(texto))[:MAX_TEXTO]


def contar() -> None:
    print(len(json.load(sys.stdin)))


def fallidas(ruta: str) -> None:
    reporte = Path(ruta)
    if not reporte.exists():
        print("[]")
        return
    nombres = []
    for caso in ET.parse(reporte).iter("testcase"):  # noqa: S314  (archivo propio)
        if caso.find("failure") is not None or caso.find("error") is not None:
            nombres.append(limpiar(f"{caso.get('classname')}::{caso.get('name')}"))
    print(json.dumps(nombres[:MAX_ELEMENTOS], ensure_ascii=False))


def leer_politica(ruta: str) -> dict[str, str]:
    politica = {}
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        if linea.strip() and not linea.startswith("#"):
            id_regla, accion, *_ = linea.split("\t")
            politica[id_regla] = accion
    return politica


def zap(ruta_reporte: str, ruta_reglas: str) -> None:
    reporte = Path(ruta_reporte)
    if not reporte.exists():
        print("[]")
        return
    politica = leer_politica(ruta_reglas)
    alertas = []
    for sitio in json.loads(reporte.read_text(encoding="utf-8")).get("site", []):
        for alerta in sitio.get("alerts", []):
            # Las alertas que no están en rules.tsv son WARN: igual que en ZAP
            accion = politica.get(alerta["pluginid"], "WARN")
            if accion == "IGNORE":
                continue
            alertas.append(
                {
                    "id": alerta["pluginid"],
                    "nombre": limpiar(alerta["name"]),
                    "riesgo": limpiar(alerta["riskdesc"]),
                    "accion": accion,
                    "instancias": int(alerta.get("count", 0)),
                }
            )
    alertas.sort(key=lambda a: a["accion"] != "FAIL")  # primero las que rompen el pipeline
    print(json.dumps(alertas[:MAX_ELEMENTOS], ensure_ascii=False))


if __name__ == "__main__":
    comando, *argumentos = sys.argv[1:]
    {"contar": contar, "fallidas": fallidas, "zap": zap}[comando](*argumentos)
