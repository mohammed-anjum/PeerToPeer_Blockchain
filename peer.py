import hashlib
import socket
import json


class Peer:
    def __init__(self, port, name, gossip_id):
        # Automatically pick up the current IP
        self.host = self.get_local_ip()
        self.port = port
        self.name = name
        self.gossip_id = gossip_id
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.received_gossipers = {}
        """
        an object containing a tuple key with host and port arrays inside a set
            {
                [height0, hash0]: ([host1,port1], [host2,port2], [host3,port3])
                [height1, hash1]: ([host1,port1], [host2,port2])
            }
        """
        self.received_stats = {}
        """
            we retain the result key of consensus 
                and plug it back in `received_stats` to get the host_port sets 
            [height, hash]
        """
        self.consensus_key = (-1, "")
        self.bad_consensus = []
        self.requested_block_heights = set()
        """
            the below will have the following format
            {
                0: (BLOCK_REPLY_1.json, BLOCK_REPLY_2.json, BLOCK_REPLY_3.json)
                1: (BLOCK_REPLY_1.json, BLOCK_REPLY_2.json)
                ...
            }
            once verified we push it to verified_blocks
            and then sql it. think
        """
        self.block_tracker = {}
        """
            the below will have the following format
            {
                0: [BLOCK_REPLY_1.json]
                1: [BLOCK_REPLY_2.json]
                ...
            }
        """
        self.verified_blocks = {}
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
        ### DO NOT REMOVE THIS PRINT
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
                        # print(f"Invalid JSON received from {addr}: {data}. Error: {e}")
                        pass

                else:
                    print(f"--LISTENING--\n\t{addr}: \n\t\tNO DATA\n")

            except Exception as e:
                # print(f"Error while receiving data: {e}")
                pass

    def handle_msg(self, addr, msg):
        """Handle received msgs."""
        host, port, msg_type, message = validate_msg(addr, msg)

        if msg_type == "GOSSIP":
            self.send_gossip_reply(host, port)
        elif msg_type == "GOSSIP_REPLY":
            self.add_gossiper(host, port, message)
        elif msg_type == "STATS_REPLY":
            self.add_stat(host, port, message)
        elif msg_type == "STATS":
            # self.send_stat_reply(host, port)
            pass
        elif msg_type == "GET_BLOCK":
            pass
        elif msg_type == "GET_BLOCK_REPLY":
            self.add_block(host, port, message)
        else:
            ### DO NOT REMOVE THIS PRINT
            # print(f"--UNKNOWN--\n\t{addr}: {message}\n")
            pass

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
            "id": self.gossip_id,
            "name": self.name
        }
        # for now i have defaulted to silicon only
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
        # print(f"--GOSSIP_REPLY_SENT--\n\tto {target_host}:{target_port}\n")

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

    # DNU
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
            the_key = (height, blk_hash)

            if the_key not in self.received_stats:
                self.received_stats[the_key] = set()
            self.received_stats[the_key].add((host, port))

            # print(f"--ADDED_STAT--\n\tfor {host}:{port}\n")

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

    # CONSENSUS ------------------------------------------------------------------------------------------------------------
    #TODO: its already in self no need for arg
    def do_consensus(self, received_stats):
        print("--DOING_CONSENSUS--")

        filtered_received_stats = [key for key in received_stats.keys() if key not in self.bad_consensus]
        if filtered_received_stats:
            highest_key = max(filtered_received_stats, key=lambda x: x[0])
            # highest_key = max(filtered_received_stats.keys(), key=lambda the_key: the_key[0])
            print(f"\t--THE_CONSENSUS--\n\t\t{highest_key}:{received_stats[highest_key]}\n")
            self.consensus_key = highest_key
    # CONSENSUS ------------------------------------------------------------------------------------------------------------

    # BLOCK ----------------------------------------------------------------------------------------------------------------
    def send_get_block(self, host, port, block_height):
        msg = {
            "type": "GET_BLOCK",
            "height": block_height
        }
        data = json.dumps(msg).encode('utf-8')
        try:
            self.socket.sendto(data, (host, port))
            self.requested_block_heights.add(block_height)  # adding heights to `set` to avoid dups
            # print(f"\t--GET_BLOCK_SENT--\n\t\tfor the height {block_height}\n\tto {host}:{port}\n")
        except Exception as e:
            print(f"--ERROR_GET_BLOCK_REQ--\n\t{e}")

    def send_get_blocks(self):
        if self.consensus_key != (-1, ""):

            consensus_height = self.consensus_key[0]
            last_block_hash = self.consensus_key[1]
            host_port_set = self.received_stats[self.consensus_key]

            for block_height in range(consensus_height):
                # TODO: next step here
                # if key not in verified_blocks
                # print(f"--GET_BLOCK_SENT-- for {block_height}")
                # print(f"\t\t{', '.join(self.verified_blocks.keys())}")
                if block_height not in self.verified_blocks:
                    # print("\t\t\tits NOT IN")
                    for host, port in host_port_set:
                        self.send_get_block(host, port, block_height)

    # listening for GET_BLOCK_REPLY
    def add_block(self, host, port, message):
        # print(f"--GET_BLOCK_REPLY--\n\tfrom: {host}:{port}")
        height_key = message["height"]
        # print(f"\t\tfor height{height_key}")
        if height_key not in self.block_tracker and height_key in range(0, self.consensus_key[0]):
            # print(f"\t\t\t{height_key} not in self.block_tracker")
            self.block_tracker[height_key] = set()
            # print(f"\t\t\t\t{height_key} > set made see {type(self.block_tracker[height_key])}")
        # {height_key: (json1, json2 ...)}
        self.block_tracker[height_key].add(json.dumps(message, sort_keys=True))
        # print(f" === Added block_json: {height_key}:{message}")
        print(f"***I have the following blocks\t\t{', '.join(self.block_tracker.keys())}")

    ## debug method
    def check_block_tracker(self):
        if len(self.block_tracker) != 0:
            ### DO NOT REMOVE THIS PRINT
            print(f"--MY_BLOCK_TRACKER--\n\t{self.block_tracker}")
        else:
            ### DO NOT REMOVE THIS PRINT
            print(f"--MY_BLOCK_TRACKER--\n\t NONE")

    ## debug method

    """
        block_tracker = the below will have the following format of the dict
        {   0: (BLOCK_REPLY_1.json, BLOCK_REPLY_1.json, BLOCK_REPLY_1.json)
            1: (BLOCK_REPLY_1.json, BLOCK_REPLY_1.json)
            ...}
        once any json in value set is verified we keep that one
        and remove the rest
        and then sql it. think
    """

    def verify_blocks(self):
        """
        Verifies blocks up to the consensus height. If a block fails verification,
        consensus is reinitiated, and dictionaries are cleared to start over.
        """
        good_consensus = True  # Flag to track if the consensus remains valid
        print("--VERIFY_BLOCKS--")

        # If verification is not yet complete (verified blocks don't match the consensus height)
        if self.consensus_key != -1 and (self.consensus_key[0] != len(self.verified_blocks)):
            # Check if we have all the blocks required for verification
            if len(self.block_tracker) == self.consensus_key[0]:
                # Iterate over block heights in order
                for height_key, set_of_block_serialized_jsons in sorted(self.block_tracker.items()):
                    # Stop verification if the consensus is already marked bad
                    if not good_consensus:
                        print("\tConsensus marked as bad. Stopping verification.")
                        break

                    # If the current block height hasn't been verified yet
                    if height_key not in self.verified_blocks:
                        print(f"\tVERIFYING: {height_key}")

                        # Determine the previous hash
                        prev_hash = "" if height_key == 0 else self.verified_blocks.get(height_key - 1, {}).get("hash",
                                                                                                                "")
                        print(f"\t\tPREV_HASH: {prev_hash}")

                        # Ensure we have a valid previous hash
                        if (height_key == 0 and prev_hash == "") or (height_key > 0 and prev_hash):
                            print("\t\t\t# Loop through set_of_block_serialized_jsons")
                            # Loop through candidate blocks at this height
                            for serialized_json_block in set_of_block_serialized_jsons:
                                # Deserialize the current block
                                json_block = json.loads(serialized_json_block)
                                print(f"\t\t\tJSON_BLOCK: {json_block}")

                                # Attempt to verify the block
                                if verification(prev_hash, json_block, 8):
                                    # If verified, add to verified blocks
                                    self.verified_blocks[height_key] = json_block
                                    print(f"\tADDED_TO_VERIFIED: {self.verified_blocks[height_key].get('height')}")
                                    break
                                else:
                                    # If block fails verification, mark consensus as bad
                                    print(f"\tNOT ADDED_TO_VERIFIED: DO_CONSENSUS")
                                    self.bad_consensus.append(self.consensus_key)
                                    good_consensus = False
                                    break
                        else:
                            # Missing previous hash; cannot proceed
                            print(f"\tMISSING PREV_HASH FOR {height_key}. Stopping verification.")
                            good_consensus = False
                            break
                    else:
                        # Block is already verified; skip it
                        print(f"\tALREADY_VERIFIED: {self.verified_blocks[height_key].get('height')}")
            else:
                # Not all blocks are present in the tracker; cannot verify
                print("# I don't have all blocks")
                print(f"\t{len(self.block_tracker)}/{self.consensus_key[0]}")
        else:
            # Verification already completed
            print("# Verification already done")

        # Clear dictionaries if consensus is bad
        if not good_consensus:
            print("--CLEARING DICTIONARIES and CONSENSUS--")
            self.consensus_key = (-1, "")
            self.verified_blocks.clear()  # Clear all verified blocks
            self.block_tracker.clear()  # Clear all block tracking data
            print("\tverified_blocks and block_tracker have been cleared.")

    # def verify_blocks(self):
    #     """
    #     Verifies blocks up to the consensus height. If a block fails verification, consensus is reinitiated.
    #     """
    #     good_consensus = True  # Flag to track if the consensus remains valid
    #     print("--VERIFY_BLOCKS--")
    #
    #     # If verification is not yet complete (verified blocks don't match the consensus height)
    #     if self.consensus_key[0] != len(self.verified_blocks):
    #         # Check if we have all the blocks required for verification
    #         if len(self.block_tracker) == self.consensus_key[0]:
    #             # Iterate over block heights in order
    #             for height_key, set_of_block_serialized_jsons in sorted(self.block_tracker.items()):
    #                 # Stop verification if the consensus is already marked bad
    #                 if not good_consensus:
    #                     print("\tConsensus marked as bad. Stopping verification.")
    #                     break
    #
    #                 # If the current block height hasn't been verified yet
    #                 if height_key not in self.verified_blocks:
    #                     print(f"\tVERIFYING: {height_key}")
    #
    #                     # Determine the previous hash
    #                     prev_hash = "" if height_key == 0 else self.verified_blocks.get(height_key - 1, {}).get("hash","")
    #                     print(f"\t\tPREV_HASH: {prev_hash}")
    #
    #                     # Ensure we have a valid previous hash
    #                     if (height_key == 0 and prev_hash == "") or (height_key > 0 and prev_hash):
    #                         print("\t\t\t# Loop through set_of_block_serialized_jsons")
    #                         # Loop through candidate blocks at this height
    #                         for serialized_json_block in set_of_block_serialized_jsons:
    #                             # Deserialize the current block
    #                             json_block = json.loads(serialized_json_block)
    #                             print(f"\t\t\tJSON_BLOCK: {json_block}")
    #
    #                             # Attempt to verify the block
    #                             if verification(prev_hash, json_block, 8):
    #                                 # If verified, add to verified blocks
    #                                 self.verified_blocks[height_key] = json_block
    #                                 print(f"\tADDED_TO_VERIFIED: {self.verified_blocks[height_key].get('height')}")
    #                                 break
    #                             else:
    #                                 # If block fails verification, mark consensus as bad
    #                                 print(f"\tNOT ADDED_TO_VERIFIED: DO_CONSENSUS")
    #                                 self.bad_consensus.append(self.consensus_key)
    #                                 self.verified_blocks.clear()
    #                                 self.block_tracker.clear()
    #                                 good_consensus = False
    #                                 break
    #                     else:
    #                         # Missing previous hash; cannot proceed
    #                         print(f"\tMISSING PREV_HASH FOR {height_key}. Stopping verification.")
    #                         good_consensus = False
    #                         break
    #                 else:
    #                     # Block is already verified; skip it
    #                     print(f"\tALREADY_VERIFIED: {self.verified_blocks[height_key].get('height')}")
    #         else:
    #             # Not all blocks are present in the tracker; cannot verify
    #             print("# I don't have all blocks")
    #             print(f"\t{len(self.block_tracker)}/{self.consensus_key[0]}")
    #     else:
    #         # Verification already completed
    #         print("# Verification already done")

    # def verify_blocks(self):
    #     good_consensus = True
    #     print("--VERIFY_BLOCKS--")
    #     # if verification not yet complete (consensus_height != verified_blocks_len)
    #     if self.consensus_key[0] != len(self.verified_blocks):
    #         # if i have all blocks (block_tracker_len == consensus_height)
    #         if len(self.block_tracker) == self.consensus_key[0]:
    #             # for height_key, set_of_block_serialized_jsons in self.block_tracker.items():
    #             for height_key, set_of_block_serialized_jsons in sorted(self.block_tracker.items()) and good_consensus:
    #                 # if this height_key is not in verified_blocks
    #                 if height_key not in self.verified_blocks:
    #                     print(f"\tVERIFYING: {height_key}")
    #                     prev_hash = "" if height_key == 0 else  self.verified_blocks.get(height_key -1).get("hash")
    #                     print(f"\t\tPREV_HASH: {prev_hash}")
    #                     if (height_key == 0 and prev_hash == "") or (height_key > 0 and prev_hash):
    #                         print("\t\t\t# loop through set_of_block_serialized_jsons")
    #                         for serialized_json_block in set_of_block_serialized_jsons:
    #                             # i - get deserialized block
    #                             json_block = json.loads(serialized_json_block)
    #                             print(f"\t\t\tJSON_BLOCK: {json_block}")
    #                             # verify(prev_hash, deserialized block, 8)
    #                             if verification(prev_hash, json_block,8):
    #                                 # add to verified_blocks
    #                                 self.verified_blocks[height_key] = json_block
    #                                 # print(f"\tADDED_TO_VERIFIED: {self.verified_blocks[height_key].get('height')}")
    #                                 break
    #                             else:
    #                                 print(f"\tNOT ADDED_TO_VERIFIED: DO_CONSENSUS")
    #                                 self.bad_consensus.append(self.consensus_key)
    #                                 good_consensus = False
    #                                 break
    #                     # else: ## go inside
    #                     #     # i dont have prev hash yet
    #                     #     pass
    #                 else:
    #                     print(f"\tALREADY_VERIFIED: {self.verified_blocks[height_key].get('height')}")
    #         else:
    #             print("# i dont have all blocks")
    #             print(f"\t{len(self.block_tracker)}/{self.consensus_key[0]}")
    #     else:
    #         print("# verification already done")


    # def verify_blocks(self):
    #     print("I AM NOW VERIFYING")
    #     if len(self.block_tracker) == int(self.consensus_key[0]):
    #         print("I AM NOW VERIFYING - NOW THAT I HAVE ALL")
    #         for height_key, set_of_block_serialized_jsons in self.block_tracker.items():
    #             if height_key not in self.verified_blocks:
    #                 if height_key == 0:
    #                     # print("--0_VERIFICATION--")
    #                     for serialized_json_block in set_of_block_serialized_jsons:
    #                         json_block = json.loads(serialized_json_block)
    #                         # print(f"\t this be a 0ish block{json_block}")
    #                         if verification("", json_block, 8):
    #                             self.verified_blocks[height_key] = json_block
    #                             # print(f"--VERIFIED_BLOCK--\n\t{self.verified_blocks[height_key]}")
    #                             break
    #                         else:
    #                             print("NOT VERIFIED 0")
    #                             # do consensus again
    #                 else:
    #                     # print("--Non0_VERIFICATION--")
    #                     prev_json_block = self.verified_blocks.get(height_key-1)
    #                     if prev_json_block:
    #                         prev_json_block_hash = prev_json_block["hash"]
    #                         for serialized_json_block in set_of_block_serialized_jsons:
    #                             json_block = json.loads(serialized_json_block)
    #                             if verification(prev_json_block_hash, json_block, 8):
    #                                 self.verified_blocks[height_key] = json_block
    #                                 # print(f"\t\t\t--VERIFIED_BLOCK--\n\t{height_key}")
    #                                 break
    #                             else:
    #                                 print("NOT VERIFIED Non0")
    #                                 # do consensus again
    #                     else:
    #                         # print("i aint got the prev yet chief")
    #                         pass
    #     else:
    #         print("I STILL DONT HAVE IT ALL")

    ## debug method
    def check_verified_blocks(self):
        if len(self.verified_blocks) != 0:
            ### DO NOT REMOVE THIS PRINT
            # print(f"--MY_BLOCK_CHAIN--\n\t{self.verified_blocks}")
            print(f"--MY_BLOCK_CHAIN--\n\t\t{len(self.verified_blocks)} ? {self.consensus_key[0]}")
        else:
            ### DO NOT REMOVE THIS PRINT
            print(f"--MY_BLOCK_CHAIN--\n\t NONE")
    ## debug method

# BLOCK ----------------------------------------------------------------------------------------------------------------

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
        # Validate hash: it must be a non-empty string and reasonably long
        if not isinstance(msg["hash"], str) or len(msg["hash"]) < 10:
            return False
        int(msg["height"])
        return True
    except (ValueError, TypeError):
        return False


def verification(previous_hash, current_block_json, difficulty=8):
    try:
        hashBase = hashlib.sha256()
        hashBase.update(previous_hash.encode())
        hashBase.update(current_block_json['minedBy'].encode())
        for message in current_block_json['messages']:
            hashBase.update(message.encode())
        hashBase.update(current_block_json['timestamp'].to_bytes(8, 'big'))
        hashBase.update(current_block_json['nonce'].encode())
        calculated_hash = hashBase.hexdigest()
        print(f"MATCHING: {calculated_hash} ? {current_block_json['hash']}")
        if calculated_hash[-difficulty:] != '0' * difficulty:
            print(f"--DIFFICULY_NO_GOOD--\n\t{calculated_hash}")
            return False
        if calculated_hash != current_block_json['hash']:
            print(f"--HASH_NO_MATCH--\n\t{calculated_hash} != {current_block_json['hash']}")
            return False

        # print(f"\t--YOUVE BEEN VERIFIED--\n\t\t{calculated_hash}")
        return True

    except KeyError as e:
        print(f"Missing key in current_block: {e}")
        return False
    except Exception as ex:
        print(f"Error during block verification: {ex}")
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


# Error during block verification: 'dict' object has no attribute 'encode'