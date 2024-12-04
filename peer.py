import socket
import json
import uuid

class Peer:
    def __init__(self, host, port, name):
        self.host = host
        self.port = port
        self.name = name
        self.peers = []  # List of known peers as (host, port) tuples
        self.gossip_history = set()  # Track UUIDs to prevent duplicates

        # Initialize the UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        print(f"Peer listening on {self.host}:{self.port}")

    def send_message(self, message, target_host, target_port):
        """Send a message to a specific peer."""
        data = json.dumps(message).encode('utf-8')
        self.socket.sendto(data, (target_host, target_port))

    def start_listening(self):
        """Start listening for incoming messages."""
        while True:
            data, addr = self.socket.recvfrom(1024)
            message = json.loads(data.decode('utf-8'))
            self.handle_message(message, addr)

    def handle_message(self, message, addr):
        """Process incoming messages."""
        msg_type = message.get("type")
        if msg_type == "GOSSIP":
            self.handle_gossip(message, addr)
        elif msg_type == "GOSSIP_REPLY":
            self.handle_gossip_reply(message, addr)
        else:
            print(f"Unknown message type from {addr}: {message}")

    def handle_gossip(self, message, addr):
        """Handle incoming gossip messages."""
        gossip_id = message["id"]
        if gossip_id in self.gossip_history:
            print(f"Duplicate gossip ignored from {addr}")
            return

        # Add to gossip history
        self.gossip_history.add(gossip_id)
        print(f"Gossip received from {addr}: {message}")

        # Send a GOSSIP_REPLY back to the sender
        reply_message = {
            "type": "GOSSIP_REPLY",
            "host": self.host,
            "port": self.port,
            "name": self.name
        }
        self.send_message(reply_message, message["host"], message["port"])

        # Forward the gossip to other peers
        for peer in self.peers:
            if peer != addr:  # Avoid sending it back to the sender
                self.send_message(message, peer[0], peer[1])

    def handle_gossip_reply(self, message, addr):
        """Handle incoming GOSSIP_REPLY messages."""
        print(f"GOSSIP_REPLY received from {addr}: {message}")

    def send_gossip(self):
        """Send a gossip message to all known peers."""
        message = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": str(uuid.uuid4()),
            "name": self.name
        }
        for peer in self.peers:
            self.send_message(message, peer[0], peer[1])
        print("Gossip message sent to peers.")