"""
Tests unitarios de la lógica del worker:
  - Exponential backoff (sin I/O real)
  - Procesamiento de mensaje: flujo normal y flujo de error → DLQ
"""

import sys
import os
import io
import json
import base64
import pytest
from unittest.mock import patch, MagicMock, call
from PIL import Image

# Variables de entorno necesarias para importar worker.py
os.environ["RABBITMQ_HOST"] = "localhost"
os.environ["RABBITMQ_USER"] = "user"
os.environ["RABBITMQ_PASS"] = "pass"
os.environ["WORKER_ID"] = "test-worker"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../services/worker"))


def imagen_a_base64(width=10, height=5) -> str:
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


class TestExponentialBackoff:
    """Verifica que conectar_rabbit usa los delays correctos antes de conectar."""

    def test_conecta_al_primer_intento(self):
        mock_conn = MagicMock()
        with patch("worker.pika.BlockingConnection", return_value=mock_conn) as mock_bc:
            with patch("worker.pika.PlainCredentials", return_value=MagicMock()):
                import worker
                conn = worker.conectar_rabbit()

        assert conn is mock_conn
        mock_bc.assert_called_once()

    def test_reintenta_con_backoff(self):
        import pika
        mock_conn = MagicMock()
        falla_y_exito = [
            pika.exceptions.AMQPConnectionError("fallo 1"),
            pika.exceptions.AMQPConnectionError("fallo 2"),
            mock_conn,
        ]

        with patch("worker.pika.PlainCredentials", return_value=MagicMock()):
            with patch("worker.pika.BlockingConnection", side_effect=falla_y_exito):
                with patch("worker.time.sleep") as mock_sleep:
                    import worker
                    conn = worker.conectar_rabbit()

        sleeps = [c.args[0] for c in mock_sleep.call_args_list]
        # Primer delay = 1s, segundo delay = 2s
        assert sleeps[0] == 1
        assert sleeps[1] == 2
        assert conn is mock_conn


class TestProcesarMensaje:
    """Verifica ACK en éxito y NACK en error."""

    def _make_mensaje(self, job_id="job-1", indice=0, fragmentos=3):
        return json.dumps({
            "job_id": job_id,
            "indice": indice,
            "imagen": imagen_a_base64(),
            "fragmentos": fragmentos,
        }).encode()

    def test_ack_en_exito(self):
        import worker

        ch = MagicMock()
        method = MagicMock()
        method.redelivered = False
        method.delivery_tag = 42

        with patch.object(worker, "publicar_resultado"):
            worker.procesar_mensaje(ch, method, None, self._make_mensaje())

        ch.basic_ack.assert_called_once_with(delivery_tag=42)
        ch.basic_nack.assert_not_called()

    def test_nack_en_error(self):
        import worker

        ch = MagicMock()
        method = MagicMock()
        method.redelivered = False
        method.delivery_tag = 99

        # Simular fallo en sobel
        with patch("worker.sobel", side_effect=RuntimeError("error de procesamiento")):
            worker.procesar_mensaje(ch, method, None, self._make_mensaje())

        ch.basic_nack.assert_called_once_with(delivery_tag=99, requeue=False)
        ch.basic_ack.assert_not_called()

    def test_publica_al_fanout(self):
        import worker

        ch = MagicMock()
        method = MagicMock()
        method.redelivered = False
        method.delivery_tag = 1

        publicados = []

        def capturar_resultado(msg):
            publicados.append(msg)

        with patch.object(worker, "publicar_resultado", side_effect=capturar_resultado):
            worker.procesar_mensaje(ch, method, None, self._make_mensaje("job-X", 2, 5))

        assert len(publicados) == 1
        assert publicados[0]["job_id"] == "job-X"
        assert publicados[0]["indice"] == 2
        assert publicados[0]["fragmentos"] == 5
