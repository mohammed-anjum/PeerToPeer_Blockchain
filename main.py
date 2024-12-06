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
    # event_q.add_event(time.time() + 33, my_peer.check_gossipers, None, 30) # debug
    event_q.add_event(time.time() + 7, my_peer.send_stats, [my_peer.received_gossipers], 10)  # send_stat
    # event_q.add_event(time.time() + 20, my_peer.check_stats, None, 20)  # debug ~ 32 it should be ready
    event_q.add_event(time.time() + 25, my_peer.do_consensus, [my_peer.received_stats], 10)
    event_q.add_event(time.time() + 35, my_peer.send_get_blocks, None, 10)
    # # # event_q.add_event(time.time() + 70, my_peer.check_block_tracker, None, 15) # debug
    event_q.add_event(time.time() + 45, my_peer.verify_blocks, None, 20)
    # event_q.add_event(time.time() + 82, my_peer.check_verified_blocks, None, 10)
    ###

    while True:
        event_q.run()

if __name__ == "__main__":
    main()