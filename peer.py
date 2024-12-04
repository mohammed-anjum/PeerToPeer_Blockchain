import socket
import json
import uuid


class Peer:
    def __init__(self, host, port, name):
        self.host = host  # The actual address this peer will use
        self.port = port  # The port for communication
        self.name = name  # Unique name for this peer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket
        self.socket.bind((self.host, self.port))  # Bind to the given host and port
        self.peers = []
        print(f"Peer started at {self.host}:{self.port}, The name: {name}")

    def send_gossip(self, target_host, target_port):
        """Send a simple gossip message."""
        print(f"Sending gossip message to {target_host}:{target_port}")
        message = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": str(uuid.uuid4()),
            "name": self.name
        }
        data = json.dumps(message).encode('utf-8')
        self.socket.sendto(data, (target_host, target_port))
        print(f"--GOSSIP_SENT--\n\tto {target_host}:{target_port}\n")

    def listen(self):
        """Listen for incoming messages."""
        print("Listening for incoming messages...")
        while True:
            data, addr = self.socket.recvfrom(1024)  # Receive data and sender address
            message = json.loads(data.decode('utf-8'))
            self.handle_message(message, addr)

    def handle_message(self, message, addr):
        """Handle received messages."""
        if message["type"] == "GOSSIP":
            print(f"--GOSSIP--\n\t{addr}: {message}\n")
        elif message["type"] == "GOSSIP_REPLY":
            print(f"--GOSSIP_REPLY--\n\t{addr}: {message}\n")
        else:
            print(f"--UNKNOWN--\n\t{addr}: {message}\n")