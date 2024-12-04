from peer import Peer
import threading
import time


def main():
    my_peer = Peer('130.179.28.124', 8993, "u-neeq name")

    # Known university peers
    UNI_PEERS = [
        ["silicon.cs.umanitoba.ca", 8999],  # website is down
        ["eagle.cs.umanitoba.ca", 8999],
        ["hawk.cs.umanitoba.ca", 8999]
    ]

    # Start listening in a separate thread
    threading.Thread(target=my_peer.listen, daemon=True).start()

    while True:
        my_peer.send_gossip(UNI_PEERS[1][0], UNI_PEERS[1][1])
        time.sleep(30) # Send gossip every 30 seconds # keep sending to maintain connection

        if len(my_peer.gossips_received) != 0:
            for key, gossiper in my_peer.gossips_received.items():
                my_peer.send_stat(gossiper['host'], gossiper['port'], gossiper['name'])
        time.sleep(30)
        print(f"**STAT_MESSAGES**\n{my_peer.stats_received}\n***********\n")

if __name__ == "__main__":
    main()
