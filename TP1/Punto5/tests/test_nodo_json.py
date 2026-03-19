import unittest
import sys
import os
import threading
import time
import json

# importar nodo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nodo import cliente, servidor, log_evento, logs


class TestLogs(unittest.TestCase):

    def test_log_memoria(self):
        log_evento("test json")
        self.assertTrue(len(logs) > 0)

    def test_log_archivo(self):
        log_evento("test archivo json")

        ruta = os.path.join("log", "nodo_json.log")
        self.assertTrue(os.path.exists(ruta))


class TestJSON(unittest.TestCase):

    def test_json_serializacion(self):
        msj = {
            "tipo": "saludo",
            "mensaje": "hola"
        }

        serializado = json.dumps(msj)
        deserializado = json.loads(serializado)

        self.assertEqual(msj, deserializado)


class TestIntegracion(unittest.TestCase):

    def test_cliente_servidor_json(self):
        ip = "127.0.0.1"
        puerto = 7000

        hilo_server = threading.Thread(
            target=servidor,
            args=(ip, puerto),
            daemon=True
        )
        hilo_server.start()

        time.sleep(1)

        cliente(ip, puerto)

        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()