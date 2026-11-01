"""Relógio e exclusão mútua da instância; não armazena dados de negócio."""

from datetime import datetime, timezone
from functools import wraps
from threading import RLock


class Contexto:
    def __init__(self, agora=None):
        self.agora = agora or (lambda: datetime.now(timezone.utc))
        self.lock = RLock()


def atomico(metodo):
    @wraps(metodo)
    def executar(self, *args, **kwargs):
        with self._contexto.lock:
            return metodo(self, *args, **kwargs)
    return executar
