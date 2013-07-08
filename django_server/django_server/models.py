from django.db import models
from django.db import transaction
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.utils import timezone
import datetime
import random as random
import config as config

import utils as utils
from libs.redis.redis_list import RedisList
from libs.redis.redis_hash_dict import RedisHashDict
from fields.list_field import ListField

class UserMeta(models.Model):
    # contains mapping of game, user to channel data
    IOS_VENDOR_CHANNEL_TYPE = 0
    FACEBOOK_CHANNEL_TYPE = 1

    game_id = models.IntegerField()
    obfuscated_user_id = models.IntegerField(blank=True, null=True)
    channel_type = models.IntegerField()  # ios or facebook channel, etc
    channel_id = models.CharField(max_length=255) # actual unique number

    def save(self, force_insert=False, force_update=False, using=None):
        """
        Add obfuscated id if it doesn't exist
        """
        # Need to save first (because on create, primary key id has not been set until after save)
        super(UserMeta, self).save(force_insert=force_insert, force_update=force_update, using=using)
        if self.obfuscated_user_id is None:
            self.obfuscated_user_id = utils.obfuscate_id(self.id)
            super(UserMeta, self).save(using=using)

    class Meta:
        unique_together = (("game_id", "channel_type", "channel_id"),)

class User(models.Model):
    # each user belongs to a particular game
    game_id = models.IntegerField()
    # there is should be a unique user_id generated for each user per game
    user_id = models.IntegerField()
    # user's username
    username = models.CharField(max_length=255)
    # user's avatar
    avatar_url = models.CharField(max_length=255)

    class Meta:
        unique_together = (("game_id", "user_id"),)

class Friend(models.Model):
    # each user belongs to a particular game
    game_id = models.IntegerField()
    # there is should be a unique user_id generated for each user per game
    user_id = models.IntegerField()
    # this will store friend user_id
    friend_id = models.IntegerField()

    class Meta:
        unique_together = (("game_id", "user_id", "friend_id"),)

class Game(models.Model):
    name = models.CharField(max_length=255)
    max_users = models.IntegerField()

class RoomInstanceManager(models.Manager):

    def join_room(self, game_id, user_id, room_id=None):
        """
        find an appropriate room to join or create one if none is available
           OR if a particular room_id is passed in, only try and join that particular room

           use last_updated in order to also include old rooms that have become zombified (users/room has timed out)
        """
        game = Game.objects.get(id=game_id)
        with transaction.commit_on_success():
            if room_id is not None:
                query_set = RoomInstance.objects.select_for_update(nowait=False).filter(id=room_id, game_id=game_id)
            else:
                query_set = RoomInstance.objects.select_for_update(nowait=False).filter(game_id=game_id)

            last_alive_time_threshold = timezone.now()-datetime.timedelta(seconds=config.ROOM_INSTANCE_TIMEOUT_SECONDS)
            query_set = query_set.filter(Q(num_users__lt=game.max_users) | Q(last_updated__lt=last_alive_time_threshold)).order_by("-num_users")

            if not len(query_set):
                if room_id is None:
                    room = RoomInstance.objects.create(game_id=game_id, num_users=1)
                else:
                    raise Exception("Unable to join room %s" % room_id)
            else:
                room = query_set[0]
                if room.last_updated < last_alive_time_threshold:
                    # resetting an old room
                    room.num_users = 1
                    room.events.delete()
                else:
                    other_user_id_list = UserInRoom.objects.filter(game_id=game_id, room_id=room.id, last_updated__gt=last_alive_time_threshold).exclude(user_id=user_id).values_list('user_id', flat=True)
                    room.num_users = len(other_user_id_list) +1

                    if room.num_users == game.max_users:
                        # setup state of room when final user joins
                        user_id_list = [int(x) for x in other_user_id_list]
                        user_id_list.append(user_id)
                        random.shuffle(user_id_list)
                        room.user_id_order = user_id_list
                        room.current_user_id = user_id_list[0]
                room.save()

            user_in_room, created = UserInRoom.objects.get_or_create(game_id=game_id, user_id=user_id, defaults={'room_id':room.id})
            if not created:
                user_in_room.room_id = room.id
                user_in_room.save()
        return room

class RoomInstance(models.Model):
    game_id = models.IntegerField()

    num_users = models.IntegerField()

    last_updated = models.DateTimeField(default=timezone.now())

    user_id_order = ListField()

    @property
    def state(self):
        return RedisHashDict("%s-%s-state" % (self.__class__.__name__, self.id))

    @property
    def current_user_id(self):
        if self.state['current_user_id'] is not None:
            return int(self.state['current_user_id'])
        else:
            return None

    @current_user_id.setter
    def current_user_id(self, value):
        self.state['current_user_id'] = value

    @property
    def events(self):
        return RedisList("%s-%s-events" % (self.__class__.__name__, self.id))

    objects = RoomInstanceManager()

    def __init__(self, *args, **kwargs):
        super(RoomInstance, self).__init__(*args, **kwargs)
        # on retrieval check whether we should expire room
        last_alive_time_threshold = timezone.now()-datetime.timedelta(seconds=config.ROOM_INSTANCE_TIMEOUT_SECONDS)
        if self.last_updated < last_alive_time_threshold:
            self.num_users = 0
            self.current_user_id = None
            self.user_id_order = None
            self.save()

    def save(self, force_insert=False, force_update=False, using=None):
        """
        refresh last_updated
        """
        self.last_updated = timezone.now()
        super(RoomInstance, self).save(force_insert=force_insert, force_update=force_update, using=using)

    class Meta:
        index_together = [
            ["game_id", "num_users"]
        ]

# delete redis data on cleanup
def room_instance_cleanup(sender, instance, *args, **kwargs):
    instance.events.delete()
    instance.state.delete()

pre_delete.connect(room_instance_cleanup, RoomInstance)

class UserInRoom(models.Model):
    game_id = models.IntegerField()
    user_id = models.IntegerField()

    room_id = models.IntegerField(null=True)
    last_updated = models.DateTimeField(default=timezone.now())

    def __init__(self, *args, **kwargs):
        super(UserInRoom, self).__init__(*args, **kwargs)
        # on retrieval check whether we should expire user record
        last_alive_time_threshold = timezone.now()-datetime.timedelta(seconds=config.ROOM_INSTANCE_TIMEOUT_SECONDS)
        if self.last_updated < last_alive_time_threshold:
            self.room_id = None
            self.save()

    def save(self, force_insert=False, force_update=False, using=None):
        """
        refresh last_updated
        """
        self.last_updated = timezone.now()
        super(UserInRoom, self).save(force_insert=force_insert, force_update=force_update, using=using)

    class Meta:
        unique_together = (("game_id", "user_id"))
        index_together = [
            ["game_id", "room_id"]
        ]