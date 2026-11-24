"""Junta el resultado de todas las etapas en resumen.json: lo único que lee n8n.

Uso (en el job "Veredicto" del pipeline):
  python3 scripts/resumen.py generar > resumen.json
  python3 scripts/resumen.py verificar resumen.json

`generar` toma los datos de variables de entorno que llena GitHub Actions.
`verificar` decide: termina en error si alguna etapa no pasó.
"""

import json
import os
import sys

ETAPAS = {
    "calidad": "Calidad y pruebas",
    "e2e": "Pruebas end-to-end",
    "zap": "Seguridad dinámica (ZAP)",
    "secretos": "Escaneo de secretos",
}
MAX_TEXTO = 200


def limpiar(texto: object) -> str:
    """Quita saltos de línea y caracteres de control, y recorta (el nombre de la rama lo elige quien abre el PR)."""
    return "".join(c if c.isprintable() else " " for c in str(texto))[:MAX_TEXTO]


def lista(texto: str | None) -> list:
    try:
        valor = json.loads(texto or "[]")
    except ValueError:
        return []
    return valor if isinstance(valor, list) else []


def entero(texto: str | None) -> int | None:
    return int(texto) if texto and texto.isdigit() else None


def generar() -> None:
    needs = json.loads(os.environ["NEEDS"])
    etapas = {}
    for clave, nombre in ETAPAS.items():
        job = needs.get(clave, {})
        salidas = job.get("outputs", {})
        etapa = {"nombre": nombre, "resultado": job.get("result", "desconocido")}
        if clave == "calidad":
            etapa["ruff_hallazgos"] = entero(salidas.get("ruff_hallazgos")) or 0
            etapa["pruebas_fallidas"] = lista(salidas.get("pruebas_fallidas"))
        elif clave == "e2e":
            etapa["pruebas_fallidas"] = lista(salidas.get("pruebas_fallidas"))
        elif clave == "zap":
            etapa["alertas"] = lista(salidas.get("alertas"))
        etapas[clave] = etapa

    servidor = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    aprobado = all(e["resultado"] == "success" for e in etapas.values())

    resumen = {
        "version": 1,
        "repo": repo,
        "run_id": entero(run_id),
        "run_url": f"{servidor}/{repo}/actions/runs/{run_id}",
        "evento": os.environ.get("GITHUB_EVENT_NAME", ""),
        "rama": limpiar(os.environ.get("RAMA", "")),
        "sha": os.environ.get("SHA", ""),
        "pr": entero(os.environ.get("PR")),
        "motivo": limpiar(os.environ["MOTIVO"]) if os.environ.get("MOTIVO") else None,
        "veredicto": "aprobado" if aprobado else "rechazado",
        "etapas": etapas,
    }
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


def verificar(ruta: str) -> None:
    with open(ruta, encoding="utf-8") as archivo:
        resumen = json.load(archivo)
    for etapa in resumen["etapas"].values():
        marca = "OK   " if etapa["resultado"] == "success" else "FALLÓ"
        print(f"{marca} {etapa['nombre']}: {etapa['resultado']}")
    print(f"Veredicto: {resumen['veredicto']}")
    sys.exit(0 if resumen["veredicto"] == "aprobado" else 1)


if __name__ == "__main__":
    comando, *argumentos = sys.argv[1:]
    {"generar": generar, "verificar": verificar}[comando](*argumentos)
