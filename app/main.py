"""Capa de API: rutas HTTP, validación de entrada y cabeceras de seguridad."""

from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import repository, services
from app.models import ConversionIn, ConversionOut, LoteIn, LoteOut

STATIC = Path(__file__).parent / "static"

app = FastAPI(
    title="Conversor de temperaturas",
    version="1.0.0",
    description="Proyecto de demostración para la Actividad #13: CI/CD con GitHub Actions y n8n.",
)

# La página no usa scripts ni estilos en línea, así que la CSP puede ser estricta.
CSP_APP = "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
# Swagger UI (/docs) carga recursos de un CDN y usa un script en línea. Es una excepción
# documentada: solo aplica a la documentación, no a la aplicación.
CSP_DOCS = (
    "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com; "
    "frame-ancestors 'none'"
)


@app.middleware("http")
async def cabeceras_de_seguridad(request: Request, call_next):
    respuesta = await call_next(request)
    es_docs = request.url.path in ("/docs", "/docs/oauth2-redirect")
    respuesta.headers["Content-Security-Policy"] = CSP_DOCS if es_docs else CSP_APP
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "no-referrer"
    respuesta.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    respuesta.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


@app.exception_handler(RequestValidationError)
async def entrada_invalida(_request: Request, exc: RequestValidationError):
    # No se repite la entrada del usuario en el error: evita reflejar datos que mandó
    # el cliente y evita un 500 cuando la entrada es NaN (no se puede convertir a JSON).
    errores = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errores})


@app.exception_handler(services.TemperaturaInvalidaError)
async def temperatura_invalida(_request: Request, exc: services.TemperaturaInvalidaError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def inicio():
    return FileResponse(STATIC / "index.html")


@app.get("/salud")
def salud():
    return {"status": "ok"}


@app.post("/conversiones", response_model=ConversionOut, status_code=201)
def crear_conversion(entrada: ConversionIn):
    resultado = services.convertir(entrada.valor, entrada.de, entrada.a, entrada.decimales)
    return repository.guardar(
        {
            "valor": entrada.valor,
            "de": entrada.de,
            "a": entrada.a,
            "resultado": resultado,
            "etiqueta": entrada.etiqueta,
        }
    )


@app.get("/conversiones", response_model=list[ConversionOut])
def listar_conversiones(limite: int = Query(default=10, ge=1, le=repository.MAX_HISTORIAL)):
    return repository.listar(limite)


@app.post("/conversiones/lote", response_model=LoteOut)
def convertir_lote(entrada: LoteIn):
    resultados = services.convertir_lote(entrada.valores, entrada.de, entrada.a, entrada.decimales)
    return {"de": entrada.de, "a": entrada.a, "resultados": resultados}
