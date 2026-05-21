"""
Tests de integración del pipeline Sobel (con RabbitMQ y Redis mockeados).

Cubren el flujo completo:
  Split publica fragmentos → Worker los consume y aplica Sobel
  → Worker publica al fanout → Joiner reconstruye → Joiner guarda en Redis
  → Backend sirve el resultado

No requieren servicios externos: pika y redis están mockeados.
"""

import sys
import os
import io
import json
import base64
import threading
import pytest
from unittest.mock import patch, MagicMock, call
from PIL import Image

os.environ["RABBITMQ_HOST"] = "localhost"
os.environ["RABBITMQ_USER"] = "user"
os.environ["RABBITMQ_PASS"] = "pass"
os.environ["WORKER_ID"] = "test-worker"
os.environ["REDIS_HOST"] = "localhost"
os.environ["SPLIT_HOST"] = "split"
os.environ["SPLIT_PORT"] = "9000"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../services/worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../services/joiner"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../services/split"))


def img_a_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def crear_imagen_test(width=30, height=15) -> Image.Image:
    img = Image.new("RGB", (width, height))
    pix = img.load()
    for y in range(height):
        for x in range(width):
            pix[x, y] = (x * 8, y * 16, 128)
    return img


class TestFlujoWorker:
    """Worker procesa un fragmento y publica al fanout correctamente."""

    def test_worker_aplica_sobel_y_publica(self):
        import worker

        imagen = crear_imagen_test(10, 5)
        mensaje = json.dumps({
            "job_id": "integ-1",
            "indice": 0,
            "imagen": img_a_b64(imagen),
            "fragmentos": 1,
        }).encode()

        ch = MagicMock()
        method = MagicMock()
        method.redelivered = False
        method.delivery_tag = 1

        publicados = []
        with patch.object(worker, "publicar_resultado", side_effect=lambda m: publicados.append(m)):
            worker.procesar_mensaje(ch, method, None, mensaje)

        assert len(publicados) == 1
        resultado = publicados[0]
        assert resultado["job_id"] == "integ-1"
        assert resultado["indice"] == 0

        # Verificar que el resultado es una imagen PNG válida en base64
        img_resultado = Image.open(io.BytesIO(base64.b64decode(resultado["resultado"])))
        assert img_resultado.mode == "L"
        assert img_resultado.size == (10, 5)

        ch.basic_ack.assert_called_once_with(delivery_tag=1)


class TestFlujoJoiner:
    """Joiner reconstruye correctamente al recibir todos los fragmentos."""

    def _simular_fragmento(self, job_id, indice, total, color):
        img = Image.new("L", (10, 5), color=color)
        return {
            "job_id": job_id,
            "indice": indice,
            "resultado": img_a_b64(img),
            "fragmentos": total,
        }

    def test_joiner_reconstruye_cuando_completo(self):
        import joiner

        redis_mock = MagicMock()
        joiner.redis_client = redis_mock
        joiner.fragmentos_por_job.clear()

        job_id = "integ-2"
        total = 3

        for i in range(total):
            msg = self._simular_fragmento(job_id, i, total, i * 80)
            ch = MagicMock()
            method = MagicMock()
            method.delivery_tag = i
            body = json.dumps(msg).encode()
            joiner.procesar_resultado(ch, method, None, body)

        # Cuando llega el último fragmento, debe guardar en Redis
        redis_calls = [str(c) for c in redis_mock.set.call_args_list]
        assert any(f"job:{job_id}:status" in c for c in redis_calls)
        assert any(f"job:{job_id}:result" in c for c in redis_calls)

        # El job debe haberse limpiado de memoria
        assert job_id not in joiner.fragmentos_por_job

    def test_joiner_no_reconstruye_antes_de_completar(self):
        import joiner

        redis_mock = MagicMock()
        joiner.redis_client = redis_mock
        joiner.fragmentos_por_job.clear()

        job_id = "integ-3"
        # Enviar solo 1 de 3 fragmentos
        msg = self._simular_fragmento(job_id, 0, 3, 128)
        ch = MagicMock()
        method = MagicMock()
        method.delivery_tag = 0

        joiner.procesar_resultado(ch, method, None, json.dumps(msg).encode())

        # Redis NO debe haberse llamado todavía
        redis_mock.set.assert_not_called()
        assert job_id in joiner.fragmentos_por_job


class TestSplitPublica:
    """Split divide correctamente y publica N fragmentos a RabbitMQ."""

    def test_divide_en_n_fragmentos(self):
        import split

        imagen = crear_imagen_test(30, 15)
        publicados = []

        mock_channel = MagicMock()
        mock_channel.basic_publish.side_effect = lambda **kw: publicados.append(
            json.loads(kw["body"])
        )

        mock_conn = MagicMock()
        mock_conn.channel.return_value = mock_channel

        with patch.object(split, "conectar_rabbit", return_value=mock_conn):
            with patch.object(split, "WORKERS", 3):
                total = split.dividir_y_publicar(imagen, "integ-4")

        assert total == 3
        assert len(publicados) == 3
        indices = sorted(f["indice"] for f in publicados)
        assert indices == [0, 1, 2]
        assert all(f["job_id"] == "integ-4" for f in publicados)

    def test_fragmentos_tienen_imagen_valida(self):
        import split

        imagen = crear_imagen_test(20, 12)
        publicados = []

        mock_channel = MagicMock()
        mock_channel.basic_publish.side_effect = lambda **kw: publicados.append(
            json.loads(kw["body"])
        )

        mock_conn = MagicMock()
        mock_conn.channel.return_value = mock_channel

        with patch.object(split, "conectar_rabbit", return_value=mock_conn):
            with patch.object(split, "WORKERS", 2):
                split.dividir_y_publicar(imagen, "integ-5")

        for frag in publicados:
            img = Image.open(io.BytesIO(base64.b64decode(frag["imagen"])))
            assert img.width == 20
            assert img.height > 0
