import json
from unittest.mock import MagicMock, patch

import publicador

def test_publicador_envia_eventos():
    mock_channel = MagicMock()
    mock_connection = MagicMock()

    with patch("pika.BlockingConnection", return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel

        publicador.main()

        # Se publican 5 mensajes
        assert mock_channel.basic_publish.call_count == 5

        # Verificar estructura del mensaje
        args, kwargs = mock_channel.basic_publish.call_args
        body = json.loads(kwargs["body"])

        assert "evento" in body
        assert body["evento"] == "nuevo_bloque"