from unittest.mock import MagicMock, patch
import json
import productor


@patch("productor.pika.BlockingConnection")
def test_productor_envia_tareas(mock_connection):
    mock_channel = MagicMock()
    mock_connection.return_value.channel.return_value = mock_channel

    productor.main()

    # Verifica que se enviaron todas las tareas
    assert mock_channel.basic_publish.call_count == len(productor.TAREAS)

    # Verifica contenido del primer mensaje
    args, kwargs = mock_channel.basic_publish.call_args_list[0]
    body = json.loads(kwargs["body"])

    assert "id" in body
    assert "descripcion" in body
    assert body["intentos"] == 0
    assert body["max_intentos"] == 4

    # Verifica exchange y routing key
    assert kwargs["exchange"] == "retry_exchange"
    assert kwargs["routing_key"] == "trabajo"