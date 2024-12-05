from event_queue import EventQueue
from peer import Peer
import threading
import uuid
import time


def main():
    my_peer = Peer(8993, "u-neeq name", str(uuid.uuid4()))
    event_q = EventQueue()

    # Start listening in a separate thread
    threading.Thread(target=my_peer.listen, daemon=True).start()

    ###
    event_q.add_event(time.time() + 1, my_peer.send_gossip, None, 30)  # send_gossip
    # event_q.add_event(time.time() + 33, my_peer.check_gossipers, None, 30) #debug
    event_q.add_event(time.time() + 20, my_peer.send_stats, [my_peer.received_gossipers], 30)  # send_stat
    event_q.add_event(time.time() + 53, my_peer.check_stats, None, 30)  # send_stat

    ###

    while True:
        event_q.run()


if __name__ == "__main__":
    main()
