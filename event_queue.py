import time

class EventQueue:

    def __init__(self):
        """events sorted by their `time_to_run`."""
        self.events = []  # List of events

    def add_event(self, time_to_run, callback, args=None, interval=None):
        """
            time_to_run (float): time.time() + X
            callback (function): The function to call when the event runs.
            args (list, optional): Arguments required by function. Defaults to None.
            interval (float, optional): At what interval it should repeat if any. Defaults to None.
        """
        event = (time_to_run, callback, args or [], interval)
        self.events.append(event)  # Add the event to the list
        self.events.sort(key=lambda x: x[0])  # Sort by `time_to_run`

    def run(self):
        while True:
            # Get the current time
            current_time = time.time()
            # Check if any events using the firsts start time
            if self.events and self.events[0][0] <= current_time:
                # Pop the one scheduled earliest
                time_to_run, callback, args, interval = self.events.pop(0)
                # Call the method
                callback(*args)
                # Reschedule it if interval given
                if interval:
                    self.add_event(current_time + interval, callback, args, interval)
            # Sleep briefly to be safe
            time.sleep(0.1)