from unittest.mock import MagicMock
import json
import etapa2.worker as worker
import base64
from PIL import Image
from pathlib import Path
import io
BASE_DIR = Path(__file__).resolve().parent
inputPath = BASE_DIR / "test.jpg"

img = Image.new("L", (10, 10))

buffer = io.BytesIO()
img.save(buffer, format="PNG")  

img_bytes = buffer.getvalue()

encoded = base64.b64encode(img_bytes).decode()

def test_worker_procesa_ok(monkeypatch):
    channel = MagicMock()
    #conexion con rabbitMQ
    mock_conn = MagicMock()
    mock_channel2 = MagicMock()
    mock_conn.channel.return_value = mock_channel2
    monkeypatch.setattr(worker, "conectar_rabbit", lambda: mock_conn)
    

    body = json.dumps({
        "indice": 1,
        "imagen": encoded,
        "fragmentos": 1,
    }).encode()

    method = MagicMock()
    method.delivery_tag = "tag"

    worker.procesar_mensaje(channel, method, None, body)

    # verifica ACK
    channel.basic_ack.assert_called_once()

    # verifica que publicó resultado
    assert mock_channel2.basic_publish.called


