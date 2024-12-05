import socket
import json
import uuid

class Peer:
    def __init__(self, port, name):
        # Automatically pick up the current IP
        self.host = self.get_local_ip()
        self.port = port
        self.name = name
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.received_gossipers = {}
        self.received_stats = {}
        print(f"Peer started at {self.host}:{self.port}, The name: {name}")

    def get_local_ip(self):
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

    def handle_message(self, addr, message):
        """Handle received messages."""
        host, port, msg_type, message = parse_and_validate(addr, message)

        if msg_type == "GOSSIP":
            print(f"--GOSSIP--\n\t{addr}: {message}\n")

        elif msg_type == "GOSSIP_REPLY":
            print(f"--GOSSIP_REPLY--\n\t{addr}: {message}\n")
            self.received_gossipers[f"{host}:{port}"] = {
                "host": host,
                "port": port,
                "name": message.get("name", "")  # Use .get to avoid KeyError
            }

        elif msg_type == "STATS_REPLY":
            print(f"--STATS_REPLY--\n\t{addr}: {message}\n")
            self.received_stats[f"{host}:{port}"] = {
                "host": host,
                "port": port,
                "height": int(message["height"]),
                "hash": message["hash"]
            }

        else:
            print(f"--UNKNOWN--\n\t{addr}: {message}\n")

    def send_gossip(self, target_host, target_port):
        """Send a simple gossip message."""
        print(f"SENDING GOSSIP to {target_host}:{target_port}")
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

    def send_stats(self, target_list):
        if len(target_list) != 0:
            for key, gossiper in target_list.items():
                self.send_stat(gossiper['host'], gossiper['port'], gossiper['name'])

    def send_stat(self, target_host, target_port, target_name):
        """Send a stats message."""
        print(f"SENDING STAT to {target_name}")
        message = {"type": "STATS"}
        data = json.dumps(message).encode('utf-8')
        self.socket.sendto(data, (target_host, target_port))
        print(f"--STATS_SENT--\n\tto {target_host}:{target_port}\n")

    def listen(self):
        """Listen for incoming messages."""
        print("Listening for incoming messages...")
        while True:
            data, addr = self.socket.recvfrom(1024)  # Receive data and sender address
            # print(f"--LISTENING--\n\t{addr}: {data}\n")
            message = json.loads(data.decode('utf-8'))
            self.handle_message(addr, message)


def parse_and_validate(addr, message):
    try:
        # Validate address
        if not isinstance(addr, tuple) or len(addr) != 2:
            raise ValueError(f"Invalid addr format: {addr}")
        host, port = addr
        if not isinstance(host, str):
            raise ValueError(f"Invalid host type: {host} (expected str)")
        if not isinstance(port, int):
            raise ValueError(f"Invalid port type: {port} (expected int)")

        # Validate message
        if not isinstance(message, dict):
            raise ValueError(f"Invalid message type: {type(message)} (expected dict)")
        if "type" not in message or not isinstance(message["type"], str):
            raise ValueError(f"Invalid or missing 'type' in message: {message}")
        msg_type = message["type"]

        return host, port, msg_type, message

    except ValueError as e:
        print(f"Validation Error: {e}")
        raise
