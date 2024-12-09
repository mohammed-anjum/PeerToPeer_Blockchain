from event_queue import EventQueue
from peer import Peer
import threading
import uuid
import time


def main():
    # change Peer core fields here
    my_peer = Peer(8993, "u-neeq name", str(uuid.uuid4()))
    # create an EventQueue
    event_q = EventQueue()

    # Start listening in a separate thread
    threading.Thread(target=my_peer.listen, daemon=True).start()

    # send gossip every 30 seconds
    event_q.add_event(time.time() + 1, my_peer.send_gossip, None, 30)
    # check on gossipers every 30 seconds as a batch ~ debug
    event_q.add_event(time.time() + 33, my_peer.check_gossipers, None, 30)
    # kick out gossipers after 60 second window, every 60 seconds
    event_q.add_event(time.time() + 61, my_peer.kick_gossiper, None, 61)
    # ask for stats every 10 seconds
    event_q.add_event(time.time() + 7, my_peer.send_stats, [my_peer.received_gossipers], 10)
    # check on stats every 10 seconds as a batch ~ debug
    event_q.add_event(time.time() + 10, my_peer.check_stats, None, 10)
    # do a consensus every 3 minutes as instructed
    event_q.add_event(time.time() + 25, my_peer.do_consensus, None, 180)
    # ask for blocks every 10 seconds
    event_q.add_event(time.time() + 30, my_peer.send_get_blocks, None, 10)
    # verify block chain every 25 seconds to see if we have a complete chain
    event_q.add_event(time.time() + 45, my_peer.verify_block_chain, None, 25)

    # uncomment to see all the blocks, WARNING will take up alot of terminal space
    # event_q.add_event(time.time() + 40, my_peer.check_block_tracker, None, 15)
    # uncomment to see verified chains blocks
    # event_q.add_event(time.time() + 60, my_peer.check_verified_blocks, None, 10)
    ###

    while True:
        event_q.run()

if __name__ == "__main__":
    main()