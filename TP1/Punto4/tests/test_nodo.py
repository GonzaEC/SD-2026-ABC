import unittest
import os
import sys
import threading
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nodo import log_evento, logs, servidor, cliente


class TestLogs(unittest.TestCase):

    def test_log_en_memoria(self):
        log_evento("Test memoria")
        self.assertTrue(len(logs) > 0)

    def test_log_en_archivo(self):
        log_evento("Test archivo")

        ruta = os.path.join("log", "nodo.log")
        self.assertTrue(os.path.exists(ruta))

        with open(ruta, "r") as f:
            contenido = f.read()

        self.assertIn("Test archivo", contenido)


class TestIntegracion(unittest.TestCase):

    def test_cliente_servidor(self):
        ip = "127.0.0.1"
        puerto = 6001  # usar otro puerto para tests

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