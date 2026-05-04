from unittest.mock import MagicMock, patch
import json
import TP3.Hit1.etapa2.joiner as joiner
import base64
from PIL import Image
from pathlib import Path
import io


BASE_DIR = Path(__file__).resolve().parent
inputPath = BASE_DIR / "test.jpg"
outputPath = BASE_DIR / "output.jpg"
img = Image.new("L", (10, 10))

buffer = io.BytesIO()
img.save(buffer, format="PNG")  

img_bytes = buffer.getvalue()

encoded = base64.b64encode(img_bytes).decode()


def test_joiner_procesa_ok(monkeypatch):
    channel = MagicMock()
    #conexion con rabbitMQ
    mock_conn = MagicMock()
    mock_channel2 = MagicMock()
    mock_conn.channel.return_value = mock_channel2
    
    monkeypatch.setattr(joiner, "output_path", str(outputPath))

    body = json.dumps({
        "indice": 0,
        "resultado": encoded,
        "fragmentos": 1
    }).encode()

    method = MagicMock()
    method.delivery_tag = "tag"

    joiner.joinResultado(channel, method, None, body)

    # verifica ACK
    channel.basic_ack.assert_called_once()
    #verificamos que se haya devuelto la imagen correctamente
    assert outputPath.exists()
