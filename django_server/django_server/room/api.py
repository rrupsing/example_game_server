from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.utils import timezone
from django.core.cache import cache

from django_server.models import *
from django_server.client_packets.event import Event
from django_server.client_packets.room import Room
from django_server.client_packets.game_update import GameUpdate
from django_server import config

class RoomManager(object):

    def __get_room_instance_cache_events_key(self, game_id, room_id):
        return "%s-%s-events"

    def __update_room_instance_cache_events_index(self, game_id, room_id, last_event_index):
        cache_key = self.__get_room_instance_cache_events_key(game_id=game_id, room_id=room_id)
        cache.set(cache_key, last_event_index)

    def __validate_user_and_room(self, game_id, user_id, room_id):
        # verify user is part of this room
        try:
            UserInRoom.objects.get(game_id=game_id, user_id=user_id, room_id=room_id)
        except UserInRoom.DoesNotExist:
            raise Exception("User not found/timed out")

        try:
            room = RoomInstance.objects.get(id=room_id, game_id=game_id)
        except RoomInstance.DoesNotExist:
            raise Exception("Room not found/timed out")

        return room

    def join_room(self, game_id, user_id, room_id=None):
        room = RoomInstance.objects.join_room(game_id=game_id, user_id=user_id, room_id=room_id)
        last_alive_time_threshold = timezone.now()-datetime.timedelta(seconds=config.ROOM_INSTANCE_TIMEOUT_SECONDS)

        # once there is a valid first user we should insert into the message queue
        if room.current_user_id is not None:
            event_data = {'user_id_order': room.user_id_order}
            event = Event(event_id=Event.ROOM_START, user_id=room.current_user_id, event_data=event_data)
        else:
            event = Event(event_id=Event.ROOM_JOIN, user_id=user_id, event_data={})

        room.events.append(event.__dict__)
        self.__update_room_instance_cache_events_index(game_id=game_id, room_id=room_id, last_event_index=len(room.events)-1)

        room = RoomInstance.objects.get(id=room.id)

        return Room(room_id=room.id, num_users=room.num_users)

    def turn_action(self, game_id, room_id, user_id, action_id, action_data):

        room = self.__validate_user_and_room(game_id=game_id, room_id=room_id, user_id=user_id)

        if user_id != room.current_user_id:
            raise Exception("It is user %s's turn" % room.current_user_id)

        event_data = {'action_id':action_id, 'action_data':action_data}
        event = Event(event_id=Event.TURN_ACTION, user_id=user_id, event_data=event_data)
        room.events.append(event.__dict__)
        self.__update_room_instance_cache_events_index(game_id=game_id, room_id=room_id, last_event_index=len(room.events)-1)

        # shift up the current user
        new_current_user_index = (room.user_id_order.index(user_id)+1) % len(room.user_id_order)
        room.current_user_id = room.user_id_order[new_current_user_index]
        return HttpResponse('')

    def poll(self, game_id, room_id, user_id, last_event_index=0):

        # check cache to see if there has been a more recent event
        cache_key = self.__get_room_instance_cache_events_key(game_id=game_id, room_id=room_id)
        most_recent_event_index = cache.get(cache_key)
        if most_recent_event_index is not None and last_event_index >= most_recent_event_index:
            return GameUpdate(events=[], next_event_index=most_recent_event_index)

        room = self.__validate_user_and_room(game_id=game_id, room_id=room_id, user_id=user_id)

        next_event_index = len(room.events)
        events = room.events[last_event_index:]
        return GameUpdate(events=events, next_event_index=next_event_index)




