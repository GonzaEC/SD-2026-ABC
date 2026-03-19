import unittest
import sys
import os
import threading
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import iniciar_grpc
from cliente import run


class TestGRPC(unittest.TestCase):

    def test_comunicacion(self):
        # levantar servidor en thread
        hilo_server = threading.Thread(target=iniciar_grpc, daemon=True)
        hilo_server.start()

        time.sleep(2)  # esperar que levante

        response = run()

        self.assertEqual(response.tipo, "respuesta")
        self.assertEqual(response.mensaje, "Hola A (cliente), soy B (servidor)")


if __name__ == "__main__":
    unittest.main()