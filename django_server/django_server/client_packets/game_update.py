from event import Event

class GameUpdate:
    def __init__(self, events, next_event_index):
        self.events = events
        self.next_event_index = next_event_index