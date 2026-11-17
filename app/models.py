"""Modelos de entrada y salida. Aquí viven los límites de cada campo."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

Escala = Literal["C", "F", "K"]

# Un número finito y en un rango razonable. Sin esto, NaN e Infinity pasan como "float".
Temperatura = Annotated[float, Field(allow_inf_nan=False, ge=-1_000_000, le=1_000_000)]

MAX_LOTE = 1000


class ConversionIn(BaseModel):
    valor: Temperatura
    de: Escala
    a: Escala
    decimales: int = Field(default=2, ge=0, le=6)
    etiqueta: str = Field(default="", max_length=40)


class ConversionOut(BaseModel):
    id: int
    valor: float
    de: Escala
    a: Escala
    resultado: float
    etiqueta: str
    fecha: datetime


class LoteIn(BaseModel):
    valores: list[Temperatura] = Field(min_length=1, max_length=MAX_LOTE)
    de: Escala
    a: Escala
    decimales: int = Field(default=2, ge=0, le=6)


class LoteOut(BaseModel):
    de: Escala
    a: Escala
    resultados: list[float]
