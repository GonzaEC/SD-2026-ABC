import threading
import requests
import time
import logging
import os

logger = logging.getLogger(__name__)

class BullyNode:
    def __init__(self, node_id: int, peers: list[dict], heartbeat_interval: int = 5, timeout: int = 3):
        """
        node_id: ID único de este nodo (int, mayor = más prioridad)
        peers: lista de otros nodos, ej: [{"id": 2, "url": "http://nodo2:8000"}, ...]
        heartbeat_interval: segundos entre cada ping al coordinador
        timeout: segundos antes de considerar que un nodo no responde
        """
        
        self.node_id = node_id
        self.peers = peers  
        self.heartbeat_interval = heartbeat_interval
        self.timeout = timeout

        self.coordinator_id = None   
        self.in_election = False    
        self.lock = threading.Lock()

    # --------------------------------------------------
    # PEERS helpers
    # --------------------------------------------------

    def get_peer_url(self, peer_id: int) -> str | None:
        for p in self.peers:
            if p["id"] == peer_id:
                return p["url"]
        return None

    def peers_with_higher_id(self):
        return [p for p in self.peers if p["id"] > self.node_id]

    def all_peers(self):
        return self.peers

    # --------------------------------------------------
    # ENVÍO DE MENSAJES
    # --------------------------------------------------

    def send_election(self, peer: dict) -> bool:
        """Manda ELECTION a un peer. Retorna True si respondió OK."""
        try:
            r = requests.post(
                f"{peer['url']}/bully/election",
                json={"sender_id": self.node_id},
                timeout=self.timeout
            )
            return r.status_code == 200
        except Exception:
            return False

    def send_coordinator(self, peer: dict):
        """Anuncia a un peer que este nodo es el nuevo coordinador."""
        try:
            requests.post(
                f"{peer['url']}/bully/coordinator",
                json={"coordinator_id": self.node_id},
                timeout=self.timeout
            )
        except Exception:
            pass 

    def ping_coordinator(self) -> bool:
        """Ping al coordinador actual. Retorna True si está vivo."""
        if self.coordinator_id is None:
            return False
        url = self.get_peer_url(self.coordinator_id)
        if url is None:
            return False
        try:
            r = requests.get(f"{url}/health", timeout=self.timeout)
            return r.status_code == 200
        except Exception:
            return False

    # --------------------------------------------------
    # ALGORITMO BULLY
    # --------------------------------------------------

    def start_election(self):
        with self.lock:
            if self.in_election:
                return  
            self.in_election = True

        logger.info(f"[Nodo {self.node_id}] Iniciando elección...")
        higher_peers = self.peers_with_higher_id()

        got_ok = False
        threads = []

        def try_peer(peer):
            nonlocal got_ok
            if self.send_election(peer):
                got_ok = True
                logger.info(f"[Nodo {self.node_id}] Recibió OK de nodo {peer['id']}")

        for peer in higher_peers:
            t = threading.Thread(target=try_peer, args=(peer,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        with self.lock:
            self.in_election = False

        if not got_ok:
            self.become_coordinator()
        else:
            logger.info(f"[Nodo {self.node_id}] Esperando anuncio de coordinador...")

    def become_coordinator(self):
        self.coordinator_id = self.node_id
        logger.info(f"[Nodo {self.node_id}] *** SOY EL NUEVO COORDINADOR ***")
        for peer in self.all_peers():
            self.send_coordinator(peer)

    def receive_coordinator(self, coordinator_id: int):
        self.coordinator_id = coordinator_id
        logger.info(f"[Nodo {self.node_id}] Nuevo coordinador reconocido: nodo {coordinator_id}")

    # --------------------------------------------------
    # HEARTBEAT LOOP (corre en background)
    # --------------------------------------------------

    def heartbeat_loop(self):
        """Loop infinito que monitorea al coordinador y dispara elecciones si cae."""
        # Al arrancar, si no hay coordinador, iniciar elección
        time.sleep(2) 
        if self.coordinator_id is None:
            self.start_election()

        while True:
            time.sleep(self.heartbeat_interval)

            if self.coordinator_id == self.node_id:
                continue

            if not self.ping_coordinator():
                logger.warning(
                    f"[Nodo {self.node_id}] Coordinador {self.coordinator_id} no responde. Iniciando elección."
                )
                self.coordinator_id = None
                self.start_election()

    def start(self):
        """Lanza el heartbeat en un hilo daemon."""
        t = threading.Thread(target=self.heartbeat_loop, daemon=True)
        t.start()
        logger.info(f"[Nodo {self.node_id}] Bully iniciado.")