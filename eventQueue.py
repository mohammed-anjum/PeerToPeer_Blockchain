# import heapq
# import time
#
# class EventQueue:
#     def __init__(self):
#         self.queue = []
#
#     def add_event(self, time_to_run, callback, *args):
#         """Add an event to the queue."""
#         heapq.heappush(self.queue, (time_to_run, callback, args))
#
#     def run(self):
#         """Run events when their time arrives."""
#         while self.queue:
#             now = time.time()
#             if self.queue[0][0] <= now:
#                 _, callback, args = heapq.heappop(self.queue)
#                 callback(*args)
#             else:
#                 time.sleep(0.1)