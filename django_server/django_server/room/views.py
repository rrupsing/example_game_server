from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from api import RoomManager

def join_room(request):
    if not request.GET.has_key('user_id') or not request.GET.has_key('game_id'):
        return HttpResponseBadRequest('Must include game_id param')

    user_id = int(request.GET['user_id'])
    game_id = int(request.GET['game_id'])

    if request.GET.has_key('room_id'):
        room_id = int(request.GET['room_id'])
    else:
        room_id = None

    room_manager = RoomManager()

    return room_manager.join_room(game_id=game_id, user_id=user_id, room_id=room_id)

def turn_action(request):
    if not request.GET.has_key('user_id') or not request.GET.has_key('game_id') or not request.GET.has_key('room_id') \
        or not request.GET.has_key('action_id') or not request.GET.has_key('action_data'):
        return HttpResponseBadRequest('Must include game_id, room_id, user_id, action_id, action_data param')

    user_id = int(request.GET['user_id'])
    game_id = int(request.GET['game_id'])
    room_id = int(request.GET['room_id'])
    action_id = int(request.GET['action_id'])
    action_data = request.GET['action_data']

    room_manager = RoomManager()

    return room_manager.turn_action(game_id=game_id, user_id=user_id, room_id=room_id, action_id=action_id, action_data=action_data)

def poll(request):
    if not request.GET.has_key('user_id') or not request.GET.has_key('game_id') or not request.GET.has_key('room_id'):
        return HttpResponseBadRequest('Must include game_id param')

    user_id = int(request.GET['user_id'])
    game_id = int(request.GET['game_id'])
    room_id = int(request.GET['room_id'])

    if request.GET.has_key('last_event_index'):
        last_event_index = request.GET['last_event_index']
    else:
        last_event_index = 0

    room_manager = RoomManager()

    return room_manager.poll(game_id=game_id, user_id=user_id, room_id=room_id, last_event_index=last_event_index)

