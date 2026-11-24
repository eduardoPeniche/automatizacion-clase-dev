"""Lógica de negocio: conversión entre Celsius, Fahrenheit y Kelvin.

Esta capa no sabe nada de HTTP ni de dónde se guardan los datos.
"""

CERO_ABSOLUTO = {"C": -273.15, "F": -459.67, "K": 0.0}


class TemperaturaInvalidaError(ValueError):
    """La temperatura está por debajo del cero absoluto de su escala."""


def a_kelvin(valor: float, escala: str) -> float:
    if escala == "C":
        return valor + 273.15
    if escala == "F":
        return (valor - 32) * 5 / 9 + 273.15
    return valor


def desde_kelvin(kelvin: float, escala: str) -> float:
    if escala == "C":
        return kelvin - 273.15
    if escala == "F":
        return (kelvin - 273.15) * 9 / 5 + 32
    return kelvin


def validar_temperatura(valor: float, escala: str) -> None:
    """Regla de negocio: nada existe por debajo del cero absoluto."""
    if valor < CERO_ABSOLUTO[escala]:
        raise TemperaturaInvalidaError(
            f"{valor} °{escala} está por debajo del cero absoluto ({CERO_ABSOLUTO[escala]} °{escala})"
        )


def convertir(valor: float, de: str, a: str, decimales: int = 2) -> float:
    validar_temperatura(valor, de)
    resultado = desde_kelvin(a_kelvin(valor, de), a)
    # round(-0.0) devuelve -0.0; sumar 0.0 lo normaliza a 0.0 para no mostrar "-0".
    return round(resultado, decimales) + 0.0


def convertir_lote(valores: list[float], de: str, a: str, decimales: int = 2) -> list[float]:
    resultados = []
    for v in valores:
        try:
            resultados.append(convertir(v, de, a, decimales))
        except:
            # Si un valor falla, se omite para no detener todo el lote
            pass
    return resultados
