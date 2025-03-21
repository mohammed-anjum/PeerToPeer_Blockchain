import hashlib
import socket
import json
import time


class Peer:
    def __init__(self, port, name, gossip_id):
        # Automatically pick up the current IP
        self.host = self.get_local_ip()
        # port is assigned in main
        self.port = port
        # name is assigned in main
        self.name = name
        # gossip id is created once for session in main using uuid
        self.gossip_id = gossip_id
        # UDP Socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        # collect all gossip reply with host:port as key
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
        # default consensus (height, last_block_hash)
        self.consensus_key = (-1, "")
        # collect all bad consesnus here to cross against when doing new consensus
        self.bad_consensus = []
        # maintain requested block heights here, avoid dups
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
        # flag to alert whether consensus is being done
        self.currently_verifying_flag = False
        # flag to alert whether we have complete chain
        self.verified_chain_flag = False
        print(f"Peer started at {self.host}:{self.port}, The name: {name}")

    def get_local_ip(self):
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

    def listen(self):
        """Listen for incoming msgs."""
        print("Listening for incoming messages...")
        while True:
            try:
                data, addr = self.socket.recvfrom(1024)
                if data:
                    try:
                        msg = json.loads(data.decode('utf-8'))  # Decode JSON
                        self.handle_msg(addr, msg)  # Process the message
                    except json.JSONDecodeError as e:
                        # print(f"Invalid JSON received from {addr}: {data}. Error: {e}")
                        pass

                else:
                    # print(f"--LISTENING--\n\t{addr}: \n\t\tNO DATA\n")
                    pass

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
            self.send_stat_reply(host, port)
        elif msg_type == "GET_BLOCK":
            self.send_block_reply(host, port, message)
        elif msg_type == "GET_BLOCK_REPLY":
            self.add_block(message)
        elif msg_type == "CONSENSUS":
            self.do_consensus()
        elif msg_type == "ANNOUNCE":
            self.add_to_verified_chain(message)
        else:
            # print(f"--UNKNOWN--\n\t{addr}: {message}\n")
            pass

    # GOSSIP ---------------------------------------------------------------------------------------------------------------
    def send_gossip(self):
        """Send a simple gossip msg TO PROF PEERS"""
        PROF_PEERS = [
            ["silicon.cs.umanitoba.ca", 8999],
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
        # hardcoded to silicon
        data = json.dumps(msg).encode('utf-8')
        self.socket.sendto(data, (PROF_PEERS[0][0], PROF_PEERS[0][1]))
        print(f"--GOSSIP_SENT--\n\tto {PROF_PEERS[0][0]}:{PROF_PEERS[0][1]}\n")

    def send_gossip_reply(self, target_host, target_port):
        """Send a gossip reply to the FROM_PEER"""
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
        """retain gossipers information"""
        self.received_gossipers[f"{host}:{port}"] = {
            "host": host,
            "port": port,
            "name": message.get("name", ""),
            "kick_time": time.time() + 60
        }
        # print(f"--ADDED_GOSSIPER--\n\t{host}:{port}\n")

    def kick_gossiper(self):
        """
        Removes gossipers whose `kick_time` is greater than or equal to the current time.
        """
        curr_time = time.time()  # Get the current time
        updated_gossipers = {}  # an empty dictionary to store valid gossipers
        for host_port, data in self.received_gossipers.items():
            if data["kick_time"] < curr_time:
                updated_gossipers[host_port] = data  # Add it to the new dictionary
        print(f"--KICKING--\n\t{len(updated_gossipers)}/{len(self.received_gossipers)} gossipers out!")
        self.received_gossipers = updated_gossipers

    ## debug method
    def check_gossipers(self):
        if len(self.received_gossipers) != 0:
            print(f"--MY_GOSSIPERS--\n\t{self.received_gossipers}")
        else:
            print(f"--MY_GOSSIPERS--\n\t NO ONE")

    ## debug method
    # GOSSIP ---------------------------------------------------------------------------------------------------------------

    # STAT -----------------------------------------------------------------------------------------------------------------
    def send_stats(self, target_list):
        """ Send stats message to list/dict of gossiped peers"""
        if len(target_list) != 0:
            for key, gossiper in target_list.items():
                self.send_stat(gossiper['host'], gossiper['port'], gossiper['name'])

    def send_stat(self, target_host, target_port, target_name):
        """Send a stats msg to gossiped peer"""
        msg = {"type": "STATS"}
        data = json.dumps(msg).encode('utf-8')
        self.socket.sendto(data, (target_host, target_port))
        # print(f"--STATS_SENT--\n\tto {target_name} - {target_host}:{target_port}\n")

    def send_stat_reply(self, target_host, target_port):
        """Send a stat reply only if we have a verified chain"""
        if self.verified_chain_flag:
            msg = {
                "host": self.host,
                "port": self.port,
                "height": self.consensus_key[0],
                "hash": self.consensus_key[1]
            }
            data = json.dumps(msg).encode('utf-8')
            self.socket.sendto(data, (target_host, target_port))
            # print(f"--STATS_REPLY_SENT--\n\tto {target_host}:{target_port}\n")

    def add_stat(self, host, port, message):
        """Record stat details to perform consensus on"""
        if stat_msg_valid(message):
            height = int(message.get("height", "0"))
            blk_hash = message.get("hash", "")
            the_key = (height, blk_hash)

            if the_key not in self.received_stats:
                # add host, port in a set to know who to contact upon consensus
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
    def do_consensus(self):
        """Perform consensus to choose chain with highest height"""
        if self.currently_verifying_flag:
            print("--UNABLE TO DO CONSENSUS AS CHAIN VERIFICATION IN PROCESS")
        else:
            print("--DOING_CONSENSUS--")
            # avoid bad faulty consesnus
            filtered_received_stats = [key for key in self.received_stats.keys() if key not in self.bad_consensus]
            if filtered_received_stats:
                # get highest
                highest_height_last_hash_key = max(filtered_received_stats, key=lambda x: x[0])
                print(f"\t--THE_CONSENSUS--\n\t\t{highest_height_last_hash_key}:{self.received_stats[highest_height_last_hash_key]}\n")
                # if we have a verified chain already
                if self.verified_chain_flag:
                    # if height is greater than current consensus height > re-sync
                    if highest_height_last_hash_key[0] > self.consensus_key[0]:
                        print("--RESYNC - CLEARING DICTIONARIES and CONSENSUS--")
                        self.verified_chain_flag = False
                        self.verified_blocks.clear()  # Clear all verified blocks
                        self.block_tracker.clear()  # Clear all block tracking data
                        self.consensus_key = highest_height_last_hash_key
                        print("\tverified_blocks and block_tracker have been cleared.")
                else:
                    self.consensus_key = highest_height_last_hash_key
    # CONSENSUS ------------------------------------------------------------------------------------------------------------

    # BLOCK ----------------------------------------------------------------------------------------------------------------
    def send_get_block(self, host, port, block_height):
        """Send a get block for specified block height to a stat host,port"""
        msg = {
            "type": "GET_BLOCK",
            "height": block_height
        }
        data = json.dumps(msg).encode('utf-8')
        try:
            self.socket.sendto(data, (host, port))
            # adding heights to `set` to avoid dups
            self.requested_block_heights.add(block_height)
            # print(f"\t--GET_BLOCK_SENT--\n\t\tfor the height {block_height}\n\tto {host}:{port}\n")
        except Exception as e:
            print(f"--ERROR_GET_BLOCK_REQ--\n\t{e}")

    def send_get_blocks(self):
        """Send get blocks for all in height range to all stat hosts,ports"""
        if self.consensus_key != (-1, ""):
            consensus_height = self.consensus_key[0]
            host_port_set = self.received_stats[self.consensus_key]
            for block_height in range(consensus_height):
                # if key not in verified_blocks
                if block_height not in self.verified_blocks:
                    for host, port in host_port_set:
                        self.send_get_block(host, port, block_height)

    def add_block(self, message):
        """Record multiple block json details according to block height"""
        height_key = message["height"]
        if height_key not in self.block_tracker and height_key in range(0, self.consensus_key[0]):
            self.block_tracker[height_key] = set()
        # json need to be serialized to add to set
        self.block_tracker[height_key].add(json.dumps(message, sort_keys=True))
        # print(f"--ADDED_BLOCK--: {height_key}")

    def send_block_reply(self, target_host, target_port, message):
        """Send a block reply only if we have a verified chain"""
        if self.verified_chain_flag:
            the_height = message["height"]
            if the_height in range(0, self.consensus_key[0]):
                msg = self.verified_blocks[message["height"]]
                data = json.dumps(msg).encode('utf-8')
                self.socket.sendto(data, (target_host, target_port))

    ## debug method
    def check_block_tracker(self):
        if len(self.block_tracker) != 0:
            print(f"--MY_BLOCK_TRACKER--\n\t{self.block_tracker}")
        else:
            print(f"--MY_BLOCK_TRACKER--\n\t NONE")
    ## debug method

    def verify_block_chain(self):
        """
        Verifies blocks up to the consensus height. If a block fails verification,
        consensus is re-initiated, and dictionaries are cleared to start over.
        """
        good_consensus = True  # Flag to track if the consensus remains valid
        print("--VERIFY_BLOCKS--")

        # If verification is not yet complete (verified blocks don't match the consensus height)
        if self.consensus_key != -1 and (self.consensus_key[0] != len(self.verified_blocks)):
            # Check if we have all the blocks required for verification
            if len(self.block_tracker) == self.consensus_key[0]:
                # we have now entered verification. No consensus allowed
                self.currently_verifying_flag = True
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
                        prev_hash = "" if height_key == 0 else self.verified_blocks.get(height_key - 1, {}).get("hash","")

                        # Ensure we have a valid previous hash
                        if (height_key == 0 and prev_hash == "") or (height_key > 0 and prev_hash):
                            # Loop through candidate blocks at this height
                            for serialized_json_block in set_of_block_serialized_jsons:
                                # Deserialize the current block
                                json_block = json.loads(serialized_json_block)

                                # Attempt to verify the block
                                if verification(prev_hash, json_block, 8):
                                    # If verified, add to verified blocks
                                    self.verified_blocks[height_key] = json_block
                                    print(f"\t\tADDED_TO_VERIFIED: {self.verified_blocks[height_key].get('height')}")
                                    # if complete chain verified
                                    if height_key == self.consensus_key[0] - 1:
                                        self.verified_chain_flag = True
                                        self.currently_verifying_flag = False
                                        print("\t\t\t--VERIFICATION COMPLETE--\n\n")
                                    break
                                else:
                                    # If block fails verification, mark consensus as bad and stop verification
                                    print(f"\tNOT ADDED_TO_VERIFIED")
                                    self.bad_consensus.append(self.consensus_key)
                                    self.currently_verifying_flag = False
                                    good_consensus = False
                                    break
                        else:
                            # Missing previous hash; cannot proceed
                            print(f"\tMISSING PREV_HASH FOR {height_key}. Stopping verification.")
                            self.currently_verifying_flag = False
                            break
                    else:
                        # Block is already verified; skip it
                        print(f"\tALREADY_VERIFIED: {self.verified_blocks[height_key].get('height')}")
            else:
                # Not all blocks are present in the tracker; cannot verify
                self.currently_verifying_flag = False
                print("--BLOCKS AVAILABLE--")
                print(f"\t{len(self.block_tracker)}/{self.consensus_key[0]}")
        else:
            # Verification already completed
            self.verified_chain_flag = True
            print("--VERIFICATION COMPLETE--\n\n")
            self.currently_verifying_flag = False

        # Clear dictionaries if consensus is bad
        if not good_consensus:
            print("--RESYNC - CLEARING DICTIONARIES and CONSENSUS--")
            self.consensus_key = (-1, "")
            self.verified_blocks.clear()  # Clear all verified blocks
            self.block_tracker.clear()  # Clear all block tracking data
            print("\tverified_blocks and block_tracker have been cleared.")
            self.do_consensus()

    ## debug method
    def check_verified_blocks(self):
        if len(self.verified_blocks) != 0:
            print(f"--MY_BLOCK_CHAIN--\n\t{self.verified_blocks}")
        else:
            print(f"--MY_BLOCK_CHAIN--\n\t NONE")
    ## debug method

# BLOCK ----------------------------------------------------------------------------------------------------------------

# ANNOUNCE -------------------------------------------------------------------------------------------------------------
    def add_to_verified_chain(self, message):
        if self.verified_chain_flag:
            if message["height"] == self.consensus_key[0]:
                if verification(self.consensus_key[1], message, 8):
                    # keep format consistent
                    message["type"] = "GET_BLOCK_REPLY"
                    self.verified_blocks[message["height"]] = message
                    print(f"--ANNOUNCEMENT_ADDED--: {message['height']}")
                else:
                    print("--BAD ANNOUNCEMENT--")
        else:
            print("Unable to add ANNOUNCEMET as my chain is incomplete")
# ANNOUNCE -------------------------------------------------------------------------------------------------------------


# UTIL ----------------------------------------------------------------------------------------------------------------
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
        print(f"Validation Error: {e}")
        raise

def stat_msg_valid(msg):
    try:
        if "height" not in msg or "hash" not in msg:
            return False
        # Validate hash: it must be a non-empty string, reasonably long and has 8 0s at minimum
        if not isinstance(msg["hash"], str) or len(msg["hash"]) < 10 or msg["hash"][-8:] != "0" * 8:
            return False
        int(msg["height"])
        return True
    except (ValueError, TypeError):
        return False

def verification(previous_hash, current_block_json, difficulty=8):
    try:
        if len(current_block_json['nonce']) > 40:
            print("Nonce is > 40 char")
            return False

        if not (1 <= len(current_block_json['messages']) <= 10):
            print("Messages not in range [1,10]")
            return False

        hashBase = hashlib.sha256()
        hashBase.update(previous_hash.encode())
        hashBase.update(current_block_json['minedBy'].encode())
        for message in current_block_json['messages']:
            if len(message) > 20:
                print("Message is > 20 char")
                return False
            hashBase.update(message.encode())
        hashBase.update(current_block_json['timestamp'].to_bytes(8, 'big'))
        hashBase.update(current_block_json['nonce'].encode())
        calculated_hash = hashBase.hexdigest()
        # print(f"MATCHING: {calculated_hash} ? {current_block_json['hash']}")
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
