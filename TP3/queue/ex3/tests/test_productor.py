from unittest.mock import Mock, patch
import productor


def test_productor_envia_mensajes():
    mock_channel = Mock()
    mock_connection = Mock()
    mock_connection.channel.return_value = mock_channel

    with patch("pika.BlockingConnection", return_value=mock_connection):
        connection = productor.pika.BlockingConnection()
        channel = connection.channel()

        for msg in productor.MENSAJES:
            channel.basic_publish(
                exchange='',
                routing_key='cola_principal',
                body=str(msg)
            )

    assert mock_channel.basic_publish.call_count == len(productor.MENSAJES)