import json
import queue
 
EXCHANGE = "fanout_test"
 
# Simula el exchange fanout: cada suscriptor tiene su propia cola
class FanoutExchange:
    def __init__(self):
        self.suscriptores = []
 
    def suscribir(self):
        q = queue.Queue()
        self.suscriptores.append(q)
        return q
 
    def publicar(self, body):
        for q in self.suscriptores:
            q.put(body)
 
def test_fanout_todos_reciben_todos_los_mensajes():
    exchange = FanoutExchange()
    cola1 = exchange.suscribir()
    cola2 = exchange.suscribir()
 
    for i in range(1, 6):
        exchange.publicar(json.dumps({"evento": "nuevo_bloque", "numero": i}))
 
    assert cola1.qsize() == 5
    assert cola2.qsize() == 5
 
    # Ambos reciben el mismo mensaje
    msg1 = json.loads(cola1.get())
    msg2 = json.loads(cola2.get())
    assert msg1 == msg2