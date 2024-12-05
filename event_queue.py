import time

class EventQueue:
    def __init__(self):
        """
        Initialize the EventQueue with an empty list.
        The list will hold events sorted by their `time_to_run`.
        """
        self.events = []  # List of events

    def add_event(self, time_to_run, callback, args=None, interval=None):
        """
        Add an event to the queue and sort it to maintain order by `time_to_run`.

        Args:
            time_to_run (float): The time (in seconds since epoch) when the event should execute.
            callback (function): The function to call when the event runs.
            args (list, optional): Arguments to pass to the callback function. Defaults to None.
            interval (float, optional): If provided, the event will repeat every 'interval' seconds.
        """
        event = (time_to_run, callback, args or [], interval)
        self.events.append(event)  # Add the event to the list
        self.events.sort(key=lambda x: x[0])  # Sort by `time_to_run`

    def run(self):
        """
        Run the EventQueue loop to process events.

        Continuously checks for events whose scheduled time has arrived.
        Executes those events and reschedules them if they are periodic.
        """
        while True:
            current_time = time.time()  # Get the current time

            # Check if there are events to process
            if self.events and self.events[0][0] <= current_time:
                # Pop the first event (the one scheduled earliest)
                time_to_run, callback, args, interval = self.events.pop(0)

                # Execute the event
                callback(*args)  # Call the function with its arguments

                # Reschedule the event if it has an interval (i.e., it is periodic)
                if interval:
                    self.add_event(current_time + interval, callback, args, interval)

            # Sleep briefly to avoid busy-waiting
            time.sleep(0.1)


"""
    For detailed documentation, you can quote:
	    •	EventBridge Scheduler: https://docs.aws.amazon.com/eventbridge/latest/userguide/scheduled-events.html
	    •	Step Functions Wait State: https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-wait-state.html
"""


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