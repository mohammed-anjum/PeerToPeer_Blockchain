from event_queue import EventQueue
from peer import Peer
import threading
import time


def main():
    my_peer = Peer(8993, "u-neeq name")
    event_q = EventQueue()

    # Known university peers
    UNI_PEERS = [
        ["silicon.cs.umanitoba.ca", 8999],  # website is down
        ["eagle.cs.umanitoba.ca", 8999],
        ["hawk.cs.umanitoba.ca", 8999]
    ]

    # Start listening in a separate thread
    threading.Thread(target=my_peer.listen, daemon=True).start()

    event_q.add_event(time.time() + 1, my_peer.send_gossip, UNI_PEERS[1], 30)
    # event_q.add_event(time.time() + 20, my_peer.send_stats, [my_peer.received_gossipers], 30)

    while True:
        event_q.run()

        if len(my_peer.received_gossipers) != 0:
            print(f"**GOSSIPERS**\n{my_peer.received_gossipers}\n***********\n")

if __name__ == "__main__":
    main()
