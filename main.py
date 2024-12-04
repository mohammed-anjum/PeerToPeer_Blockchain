from peer import Peer
import threading
import time

def main():
    # Initialize the peer
    my_peer = Peer("aviary.cs.umanitoba.ca", 8999, "MyPeerName")

    # Add known university peers
    my_peer.peers = [
        ("silicon.cs.umanitoba.ca", 8999),
        ("eagle.cs.umanitoba.ca", 8999),
        ("hawk.cs.umanitoba.ca", 8999)
    ]

    # Start listening in a separate thread
    threading.Thread(target=my_peer.listen(), daemon=True).start()

    # Send gossip every 30 seconds
    while True:
        my_peer.send_gossip(my_peer.peers[1][0], my_peer.peers[1][1])
        time.sleep(30)

if __name__ == "__main__":
    main()