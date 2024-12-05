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
        self.uni_peer = [] # we will implement this later
        self.GOSSIP_MSG = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": str(uuid.uuid4()),
            "name": self.name
        }
        ### DO NOT REMOVE THIS PRINT
        print(f"Peer started at {self.host}:{self.port}, The name: {name}")

    def get_local_ip(self):
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

    def handle_msg(self, addr, msg):
        """Handle received msgs."""
        host, port, msg_type, message = validate_msg(addr, msg)

        if msg_type == "GOSSIP":
            self.send_gossip_reply(host, port)

        elif msg_type == "GOSSIP_REPLY":
            #print(f"--GOSSIP_REPLY--\n\t{addr}: {message}\n")
            self.received_gossipers[f"{host}:{port}"] = {
                "host": host,
                "port": port,
                "name": message.get("name", "")  # Use .get to avoid KeyError
            }
            #print(f"--ADDED_GOSSIPER--\n\t{addr}: {message}\n")

        elif msg_type == "STATS_REPLY":
            #print(f"--STATS_REPLY--\n\t{addr}: {message}\n")
            if stat_msg_valid(message):
                self.received_stats[f"{host}:{port}"] = {
                    "host": host,
                    "port": port,
                    "height": int(message.get("height", "0")),
                    "hash": message["hash"]
                }
        elif msg_type == "STATS":
            pass

        else:
            ### DO NOT REMOVE THIS PRINT
            print(f"--UNKNOWN--\n\t{addr}: {message}\n")

    def send_gossip(self):
        """Send a simple gossip msg TO UNI PEERS"""

        UNI_PEERS = [
            ["silicon.cs.umanitoba.ca", 8999],  # website is down
            ["eagle.cs.umanitoba.ca", 8999],
            ["hawk.cs.umanitoba.ca", 8999],
            ["grebe.cs.umanitoba.ca", 8999],
            ["goose.cs.umanitoba.ca", 8999]
        ]

        # for now i have defaulted to eagle only
        data = json.dumps(self.GOSSIP_MSG).encode('utf-8')
        self.socket.sendto(data, (UNI_PEERS[1][0], UNI_PEERS[1][1]))
        ### DO NOT REMOVE THIS PRINT
        print(f"--GOSSIP_SENT--\n\tto {UNI_PEERS[1][0]}:{UNI_PEERS[1][1]}\n")

    def send_gossip_reply(self, target_host, target_port):
        """Send a gossip reply to FROM peer"""
        # print(f"SENDING GOSSIP_REPLY to {target_host}:{target_port}")
        msg = {
            "type": "GOSSIP_REPLY",
            "host": self.host,
            "port": self.port,
            "name": self.name
        }
        data = json.dumps(msg).encode('utf-8')
        self.socket.sendto(data, (target_host, target_port))
        #print(f"--GOSSIP_REPLY_SENT--\n\tto {target_host}:{target_port}\n")

    def send_stats(self, target_list):
        if len(target_list) != 0:
            for key, gossiper in target_list.items():
                self.send_stat(gossiper['host'], gossiper['port'], gossiper['name'])

    def send_stat(self, target_host, target_port, target_name):
        """Send a stats msg."""
        #print(f"SENDING STAT to {target_name}")
        msg = {"type": "STATS"}
        data = json.dumps(msg).encode('utf-8')
        self.socket.sendto(data, (target_host, target_port))
        #print(f"--STATS_SENT--\n\tto {target_host}:{target_port}\n")

    ## debug method
    def check_gossipers(self):
        if len(self.received_gossipers) != 0:
            ### DO NOT REMOVE THIS PRINT
            print(f"--MY_GOSSIPERS--\n\t{self.received_gossipers}")
        else:
            ### DO NOT REMOVE THIS PRINT
            print(f"--MY_GOSSIPERS--\n\t NO ONE")
    ## debug method

    def listen(self):
        """Listen for incoming msgs."""
        ### DO NOT REMOVE THIS PRINT
        print("Listening for incoming messages...")
        while True:
            data, addr = self.socket.recvfrom(1024)  # Receive data and sender address
            #print(f"--LISTENING--\n\t{addr}: {data}\n")
            msg = json.loads(data.decode('utf-8'))
            self.handle_msg(addr, msg)


def validate_msg(addr, msg):
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
        if not isinstance(msg, dict):
            raise ValueError(f"Invalid message type: {type(msg)} (expected dict)")
        if "type" not in msg or not isinstance(msg["type"], str):
            raise ValueError(f"Invalid or missing 'type' in message: {msg}")
        msg_type = msg["type"]

        return host, port, msg_type, msg

    except ValueError as e:
        ### DO NOT REMOVE THIS PRINT
        print(f"Validation Error: {e}")
        raise


def stat_msg_valid(msg):
    try:
        if "height" not in msg or "hash" not in msg:
            return False
        int(msg["height"])
        return True
    except (ValueError, TypeError):
        return False


"""
## update this in send_gossip

for each host, port in known_hosts:
    try:
        attempt sendto for this host and port
        if successful, break the loop
    except error:
        log failure for this host
        continue to the next host

if all attempts failed:
    handle the failure case

also create a peer field to keep track of the successful one and then use that as priority
"""
