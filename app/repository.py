"""Historial de conversiones en memoria.

Guarda solo las últimas MAX_HISTORIAL para que el historial no crezca sin límite.
"""

from collections import deque
from datetime import UTC, datetime
from itertools import count
from threading import Lock

MAX_HISTORIAL = 50

_historial: deque[dict] = deque(maxlen=MAX_HISTORIAL)
_ids = count(1)
_lock = Lock()


def guardar(registro: dict) -> dict:
    with _lock:
        nuevo = {"id": next(_ids), "fecha": datetime.now(UTC), **registro}
        _historial.appendleft(nuevo)
    return nuevo


def listar(limite: int) -> list[dict]:
    with _lock:
        return list(_historial)[:limite]


def limpiar() -> None:
    """Solo para pruebas: deja el historial vacío y reinicia los ids."""
    global _ids
    with _lock:
        _historial.clear()
        _ids = count(1)
