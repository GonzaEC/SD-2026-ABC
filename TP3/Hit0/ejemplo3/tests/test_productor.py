from unittest.mock import Mock, patch
import productor


@patch("productor.pika.BlockingConnection")
def test_productor_envia_mensajes(mock_connection):
    mock_channel = Mock()
    mock_connection.return_value.channel.return_value = mock_channel

    productor.main()

    # Se deberían enviar todos los mensajes
    assert mock_channel.basic_publish.call_count == len(productor.MENSAJES)