# Peer-to-Peer Blockchain System Documentation

This document provides an overview of the design and functionality of the peer-to-peer blockchain system, highlighting key aspects such as the event queue, consensus process, peer removal, re-syncing mechanisms, and hardcoded configurations.

## **To run the project, please run the following command:**
```
python3 main.py
```

---

## **1. Event Queue**
### **Purpose**
The event queue is designed to handle communication between peers efficiently, ensuring message-based interaction for tasks like gossiping, consensus, and block sharing.

### **Inspiration**
Inspired by AWS EventBridge Scheduler and Step Functions

- AWS **EventBridge Scheduler** enables time-based and recurring event triggers, making it suitable for tasks requiring periodic execution or time-based workflows.
    - Documentation: [EventBridge Scheduler](https://docs.aws.amazon.com/eventbridge/latest/userguide/scheduled-events.html)

- AWS **Step Functions Wait State** allows you to introduce time delays within workflows, enabling precise control over event timing.
    - Documentation: [Step Functions Wait State](https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-wait-state.html)


### **Core Responsibilities**
- **Message Validation**:
  - Messages are validated using the `validate_msg` function to ensure integrity.
  - Incorrectly formatted messages are ignored.
- **Message Types**:
  - Handles different message types such as:
    - **GOSSIP**: Peer discovery.
    - **STATS**: Peer stats exchange.
    - **GET_BLOCK**: Requests for specific blockchain blocks.
    - **CONSENSUS**: Triggers consensus mechanism.
    - **ANNOUNCE**: New verified block announcement.

---

## **2. Consensus Process**
### **Purpose**
The consensus process determines the blockchain with the highest height (most blocks) among peers.

### **How It Works**
1. **Received Stats**:
   - Maintains a dictionary `received_stats`:
     ```python
     received_stats = {
         (height, hash): {(host1, port1), (host2, port2)}
     }
     ```
   - Each key is a tuple `(height, hash)` representing a potential consensus, and the value is a set of peer addresses supporting that consensus.

2. **Choosing Consensus**:
   - Filters out bad consensuses (recorded in `bad_consensus`). Bad consensus are found during block verification failures in `verify_block_chain()` method
   - Selects the chain with the **highest height** using:
     ```python
     max(filtered_received_stats, key=lambda x: x[0])
     ```

3. **Re-Synchronization**:
   - If the new consensus height is greater than the current height, the system clears:
     - `verified_blocks`: The verified blockchain data.
     - `block_tracker`: Tracks incoming blocks for verification.
   - Updates the `consensus_key` to the new highest chain.

4. **Verification**:
   - Once blocks are retrieved for the selected consensus, verification checks ensure the chain's validity using `verification(previous_hash, current_block_json)`.

---

## **3. Peer Removal**
### **Purpose**
Peers that fail to respond or are inactive are removed to ensure the network remains reliable.

### **Mechanism**
1. **Tracking Peers**:
   - Peers are tracked in `received_gossipers`:
     ```python
     received_gossipers = {
         "host:port": {
             "host": str,
             "port": int,
             "kick_time": timestamp,
         }
     }
     ```
   - Each peer has a `kick_time` after which they are considered inactive.

2. **Kicking Peers**:
   - Periodically checks all peers using `kick_gossiper`:
     ```python
     if data["kick_time"] < curr_time:
         del self.received_gossipers[host_port]
     ```

---

## **4. Re-Sync Process**
### **Purpose**
To recover from a failed consensus or incomplete chain by re-synchronizing blocks.

### **Mechanism**
1. **Block Requests**:
   - Sends `GET_BLOCK` messages for all missing blocks to peers supporting the current consensus:
     ```python
     for block_height in range(consensus_height):
         if block_height not in self.verified_blocks:
             for host, port in self.received_stats[self.consensus_key]:
                 self.send_get_block(host, port, block_height)
     ```

2. **Verification and Storage**:
   - Once received, blocks are verified and stored in `verified_blocks`.

3. Additionally flags help us ensure the resync process communicates with the correct methods
   - `self.currently_verifying_flag = False` = flag to alert whether chain verification is being done and therefore prevent any consensus
   - `self.verified_chain_flag = False` = flag to alert whether we have complete chain
   - 

---

## **5. Hardcoded Configurations**
### **main.py**
- **Peers fields**:
  - The system uses hardcoded peer fields can be changed here in line 10:
    ```python
    Peer(8993, "u-neeq name", str(uuid.uuid4()))
    ```
  * Port
  * name
  * gossip ID


### **Peer.py**
- **Default Peers**:
  - The system uses hardcoded peer addresses for initial communication (`PROF_PEERS`):
    ```python
            PROF_PEERS = [
                ["silicon.cs.umanitoba.ca", 8999],
                ["eagle.cs.umanitoba.ca", 8999],
                ["hawk.cs.umanitoba.ca", 8999],
                ["grebe.cs.umanitoba.ca", 8999],
                ["goose.cs.umanitoba.ca", 8999]
            ]
    ```
  - Used to bootstrap the network and initiate gossip.

- **Debug Prints**:
- Due to many peers sending incomplete or incorrect messages, i have purposely commented out certain exception, error-handling print messages in `except` and `else` blocks and used `pass` instead. you may uncomment them to fully test error handling prints. This change does not affect the error handling itself, just the display
