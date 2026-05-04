from unittest.mock import MagicMock, patch
import json
import TP3.Hit1.etapa2.splitter as splitter
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
inputPath = BASE_DIR / "FondoCristiano.jpg"

@patch("splitter.pika.BlockingConnection")
@patch("sys.argv", ["splitter.py", inputPath, "output.jpg"])
def test_splitter_envia_tareas(mock_connection):
    mock_channel = MagicMock()
    mock_connection.return_value.channel.return_value = mock_channel
    
    splitter.main()
    cantidadEsperada = 3
    # Verifica que se enviaron todas las tareas
    assert mock_channel.basic_publish.call_count == cantidadEsperada

    # Verifica contenido de los mensajes (3)
    for i in range(3):
            args, kwargs = mock_channel.basic_publish.call_args_list[i]
            body = json.loads(kwargs["body"])

            assert ('indice' in body) and (body["indice"] == i)
            assert "imagen" in body
            assert body["fragmentos"] == 3
            
