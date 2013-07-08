from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import render_to_response
from models import UserMeta, User, RoomInstance, UserInRoom, Game
from django.core import serializers
import datetime
import time
import json
from django.core import serializers
from client_packets.event import Event
from client_packets.room import Room

def get_or_create_user(request):
    user_id = None
    ios_vendor_id = None
    facebook_id = None

    if not request.GET.has_key('game_id'):
        return HttpResponseBadRequest('Must include game_id param')

    game_id = request.GET['game_id']

    if request.GET.has_key('ios_vendor_id'):
        ios_vendor_id = request.GET['ios_vendor_id']
    if request.GET.has_key('facebook_id'):
        facebook_id = request.GET['facebook_id']
    if request.GET.has_key('user_id'):
        user_id = request.GET['user_id']

    # they're requesting a user
    if user_id is not None:
        user = User.objects.get(game_id=game_id, user_id=user_id)
    else:
        # they're creating a user
        # vendor_id or facebook_id must be non empty!
        if ios_vendor_id is None and facebook_id is None:
            return HttpResponseBadRequest('Must include at least one of vendor_id or facebook_id param')

        # they could be creating a new record relating a user_id to a facebook or vendor id
        # OR they could be retrieving an existing record and re-using it
        if ios_vendor_id is not None:
            user_meta, created = UserMeta.objects.get_or_create(game_id=game_id, channel_type=UserMeta.IOS_VENDOR_CHANNEL_TYPE, channel_id=ios_vendor_id)
        else:
            user_meta, created = UserMeta.objects.get_or_create(game_id=game_id, channel_type=UserMeta.FACEBOOK_CHANNEL_TYPE, channel_id=facebook_id)

        user, user_created = User.objects.get_or_create(game_id=game_id, user_id=user_meta.obfuscated_user_id)

    # return a user packet back to the client
    data = serializers.serialize("json", [user], fields=('game_id', 'user_id', 'username', 'avatar_url'))

    return HttpResponse(data, content_type="application/json")

def get_friends(request):

    if not request.GET.has_key('game_id') or not request.GET.has_key('user_id'):
        return HttpResponseBadRequest('Must include game_id, user_id param')

    game_id = request.GET['game_id']
    user_id = request.GET['user_id']

    friends = Friend.objects.filter(game_id=game_id, user_id=user_id)

     # return a packet back to the client
    data = serializers.serialize("json", [friends], fields=('game_id', 'friend_id'))

    return HttpResponse(data, content_type="application/json")

