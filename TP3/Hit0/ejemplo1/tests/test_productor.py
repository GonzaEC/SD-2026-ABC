import json
from unittest.mock import MagicMock, patch

import productor

def test_productor_envia_mensajes():
    mock_channel = MagicMock()
    mock_connection = MagicMock()

    # Mock de conexión
    with patch("pika.BlockingConnection", return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel

        # Ejecutar main
        productor.main()

        # Verificar que se enviaron mensajes
        assert mock_channel.basic_publish.call_count == 10