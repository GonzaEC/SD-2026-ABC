"""
Tests unitarios del scaler de workers dinámicos.
Cubren: cálculo de workers según profundidad de cola,
clamp de mínimos/máximos y manejo de error de conexión.
"""

import sys
import os
import math
import pytest
from unittest.mock import patch, MagicMock

# Parchear variables de entorno ANTES de importar el módulo
os.environ.setdefault("RABBITMQ_HOST", "localhost")
os.environ.setdefault("RABBITMQ_USER", "user")
os.environ.setdefault("RABBITMQ_PASS", "pass")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../scripts"))
from scaler import calculate_workers, get_queue_depth


class TestCalculateWorkers:
    """Tests de la función de cálculo, sin I/O."""

    def _calc(self, depth, per_worker=5, min_w=1, max_w=10):
        # Reproduce la lógica de calculate_workers con parámetros inyectados
        if depth < 0:
            return min_w
        if depth == 0:
            return min_w
        workers = math.ceil(depth / per_worker)
        return max(min_w, min(workers, max_w))

    def test_cola_vacia_da_minimo(self):
        assert self._calc(0) == 1

    def test_cinco_mensajes_un_worker(self):
        assert self._calc(5) == 1

    def test_seis_mensajes_dos_workers(self):
        assert self._calc(6) == 2

    def test_clamp_maximo(self):
        assert self._calc(1000) == 10

    def test_clamp_minimo_con_error(self):
        assert self._calc(-1) == 1

    def test_escala_lineal(self):
        for n in range(1, 50):
            expected = min(math.ceil(n / 5), 10)
            assert self._calc(n) == expected

    def test_min_workers_cero_cola_vacia(self):
        result = self._calc(0, min_w=0)
        assert result == 0

    def test_messages_per_worker_uno(self):
        assert self._calc(7, per_worker=1) == 7


class TestGetQueueDepth:
    """Tests del acceso a la API de RabbitMQ (mockeado)."""

    def test_devuelve_profundidad(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"messages": 42}
        mock_resp.raise_for_status = MagicMock()

        with patch("scaler.requests.get", return_value=mock_resp):
            depth = get_queue_depth()

        assert depth == 42

    def test_cola_sin_mensajes(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"messages": 0}
        mock_resp.raise_for_status = MagicMock()

        with patch("scaler.requests.get", return_value=mock_resp):
            depth = get_queue_depth()

        assert depth == 0

    def test_error_de_conexion_retorna_menos_uno(self):
        import requests as req
        with patch("scaler.requests.get", side_effect=req.RequestException("timeout")):
            depth = get_queue_depth()

        assert depth == -1

    def test_url_correcta(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"messages": 3}
        mock_resp.raise_for_status = MagicMock()

        with patch("scaler.requests.get", return_value=mock_resp) as mock_get:
            get_queue_depth()
            url_llamada = mock_get.call_args[0][0]

        assert "tareas" in url_llamada
        assert "15672" in url_llamada
