class Event:
    ROOM_JOIN = 1
    ROOM_START = 2
    TURN_ACTION = 3

    def __init__(self, event_id, user_id, event_data):
        self.event_id = event_id
        self.user_id = user_id
        self.event_data = event_data