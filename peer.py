import socket
import json


class Peer:
    def __init__(self, port, name, id):
        # Automatically pick up the current IP
        self.host = self.get_local_ip()
        self.port = port
        self.name = name
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.received_gossipers = {}
        self.received_stats = {}
        self.id = id
        ### DO NOT REMOVE THIS PRINT
        print(f"Peer started at {self.host}:{self.port}, The name: {name}")

    def get_local_ip(self):
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

    # def listen(self):
    #     """Listen for incoming msgs."""
    #     ### DO NOT REMOVE THIS PRINT
    #     print("Listening for incoming messages...")
    #     while True:
    #         data, addr = self.socket.recvfrom(1024)  # Receive data and sender address
    #         if data:
    #             print(f"--LISTENING--\n\t{addr}: {data}\n")
    #             msg = json.loads(data.decode('utf-8'))
    #             self.handle_msg(addr, msg)
    #         else:
    #             print(f"--LISTENING--\n\t{addr}: \n\t\tNO DATA\n")
    #             pass

    def listen(self):
        """Listen for incoming msgs."""
        print("Listening for incoming messages...")
        while True:
            try:
                data, addr = self.socket.recvfrom(1024)  # Receive data and sender address

                if data:
                    # print(f"--LISTENING--\n\t{addr}: {data}\n")

                    # Attempt to decode JSON only if data is non-empty
                    try:
                        msg = json.loads(data.decode('utf-8'))  # Decode JSON
                        self.handle_msg(addr, msg)  # Process the message
                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON received from {addr}: {data}. Error: {e}")

                else:
                    print(f"--LISTENING--\n\t{addr}: \n\t\tNO DATA\n")

            except Exception as e:
                print(f"Error while receiving data: {e}")

    def handle_msg(self, addr, msg):
        """Handle received msgs."""
        host, port, msg_type, message = validate_msg(addr, msg)

        if msg_type == "GOSSIP":
            self.send_gossip_reply(host, port)
        elif msg_type == "GOSSIP_REPLY":
            self.add_gossiper(host, port, message)
        elif msg_type == "STATS_REPLY":
            print("\n!!! We got a STATS_REPLY !!!\n")
            self.add_stat(host, port, message)
        elif msg_type == "STATS":
            self.send_stat_reply(host, port)
        else:
            ### DO NOT REMOVE THIS PRINT
            print(f"--UNKNOWN--\n\t{addr}: {message}\n")

# GOSSIP ---------------------------------------------------------------------------------------------------------------
    def send_gossip(self):
        """Send a simple gossip msg TO PROF PEERS"""
        PROF_PEERS = [
            ["silicon.cs.umanitoba.ca", 8999],  # website is down
            ["eagle.cs.umanitoba.ca", 8999],
            ["hawk.cs.umanitoba.ca", 8999],
            ["grebe.cs.umanitoba.ca", 8999],
            ["goose.cs.umanitoba.ca", 8999]
        ]
        msg = {
            "type": "GOSSIP",
            "host": self.host,
            "port": self.port,
            "id": self.id,
            "name": self.name
        }
        # for now i have defaulted to eagle only
        data = json.dumps(msg).encode('utf-8')
        self.socket.sendto(data, (PROF_PEERS[0][0], PROF_PEERS[0][1]))
        ### DO NOT REMOVE THIS PRINT
        print(f"--GOSSIP_SENT--\n\tto {PROF_PEERS[0][0]}:{PROF_PEERS[0][1]}\n")

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

    def add_gossiper(self, host, port, message):
        # print(f"--GOSSIP_REPLY--\n\t{addr}: {message}\n")
        self.received_gossipers[f"{host}:{port}"] = {
            "host": host,
            "port": port,
            "name": message.get("name", "")  # Use .get to avoid KeyError
        }
        # print(f"--ADDED_GOSSIPER--\n\t{addr}: {message}\n")

    ## debug method
    def check_gossipers(self):
        if len(self.received_gossipers) != 0:
            ### DO NOT REMOVE THIS PRINT
            print(f"--MY_GOSSIPERS--\n\t{self.received_gossipers}")
        else:
            ### DO NOT REMOVE THIS PRINT
            print(f"--MY_GOSSIPERS--\n\t NO ONE")
    ## debug method
# GOSSIP ---------------------------------------------------------------------------------------------------------------

# STAT -----------------------------------------------------------------------------------------------------------------
    def send_stats(self, target_list):
        if len(target_list) != 0:
            for key, gossiper in target_list.items():
                self.send_stat(gossiper['host'], gossiper['port'], gossiper['name'])

    def send_stat(self, target_host, target_port, target_name):
        """Send a stats msg."""
        # print(f"SENDING STAT to {target_name}")
        msg = {"type": "STATS"}
        data = json.dumps(msg).encode('utf-8')
        self.socket.sendto(data, (target_host, target_port))
        # print(f"--STATS_SENT--\n\tto {target_host}:{target_port}\n")

    def send_stat_reply(self, target_host, target_port):
        msg = {
                "host": self.host,
                "port": self.port,
                "height": -1,
                "hash": ""
            }
        data = json.dumps(msg).encode('utf-8')
        self.socket.sendto(data, (target_host, target_port))
        # print(f"--STATS_REPLY_SENT--\n\tto {target_host}:{target_port}\n")

    def add_stat(self, host, port, message):
        if stat_msg_valid(message):
            height = int(message.get("height", "0"))
            blk_hash = message.get("hash", "")
            the_key = (blk_hash, height)

            if the_key not in self.received_stats:
                self.received_stats[the_key] = set()
            self.received_stats[the_key].add((host, port))

            print(f"--ADDED_STAT--\n\tfor {host}:{port}\n")

    # def add_stat(self, host, port, message):
    #     print(f"--STATS_REPLY--\n\t{host}:{port} = {message}\n")
    #     if stat_msg_valid(message):
    #         self.received_stats[f"{host}:{port}"] = {
    #             "host": host,
    #             "port": port,
    #             "height": int(message.get("height", "0")),
    #             "hash": message["hash"]
    #         }
    #     print(f"--ADDED_STAT--\n\tfor {host}:{port}\n")

    ## debug method
    def check_stats(self):
        if len(self.received_stats) != 0:
            ### DO NOT REMOVE THIS PRINT
            print(f"--MY_STATS--\n\t{self.received_stats}")
        else:
            ### DO NOT REMOVE THIS PRINT
            print(f"--MY_STATS--\n\t NONE")
    ## debug method
# STAT -----------------------------------------------------------------------------------------------------------------

# # CONSENSUS ------------------------------------------------------------------------------------------------------------
    def do_consensus(self, received_stats):
        print("--DOING_CONSENSUS--")
        highest_key = max(received_stats.keys(), key=lambda the_key: the_key[0])
        print(f"--THE_CONSENSUS--\n\t{highest_key}:{received_stats[highest_key]}\n")
        return highest_key

#     def find_consensus(self, received_stats):
#         # Create a dictionary to count occurrences of each (height, hash) pair
#         counts = {}
#         for peer, data in received_stats.items():
#             key = (data["height"], data["hash"]) # tuple as a key
#             counts[key] = counts.get(key, 0) + 1 # gets the curr count value and adds 1
#
#         # Find the most agreed-upon pair
#         consensus = max(counts.items(), key=lambda x: x[1])  # x[1] is the count
#         return consensus[0]  # Returns (height, hash)
# # CONSENSUS ------------------------------------------------------------------------------------------------------------

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
    
add this to peer obj `self.uni_peer = [] # we will implement this later`

also create a peer field to keep track of the successful one and then use that as priority
"""
