import unittest
from models import *
import config as config
import time
from room.tests import *

class RoomInstanceManagerTestCase(unittest.TestCase):
    """
    Test models functions
    """
    def setUp(self):
        self.game_id = 1
        self.user_id = 2

        self.room_manager = RoomInstanceManager()

        self.game = Game.objects.create(id=self.game_id, name='C4', max_users=2)

        config.ROOM_INSTANCE_TIMEOUT_SECONDS = 2

    def tearDown(self):
        User.objects.all().delete()
        UserMeta.objects.all().delete()
        Game.objects.all().delete()
        RoomInstance.objects.all().delete()
        UserInRoom.objects.all().delete()

    def testRoomJoin(self):

        room = self.room_manager.join_room(game_id=self.game_id, user_id=self.user_id)

        self.assertIsNotNone(room)

        db_room = RoomInstance.objects.get(id=room.id)
        self.assertEquals(room.id, db_room.id)
        self.assertEquals(room.num_users, 1)
        self.assertEquals(db_room.num_users, 1)
        self.assertEquals(db_room.game_id, self.game_id)

        user_in_room = UserInRoom.objects.get(game_id=self.game_id, user_id=self.user_id)
        self.assertEquals(user_in_room.room_id, room.id)

        # try joining again with a different user
        user_id2 = self.user_id+1
        room2 = self.room_manager.join_room(game_id=self.game_id, user_id=user_id2)

        self.assertEqual(room.id, room2.id)
        self.assertEqual(room2.num_users, 2)

        user_in_room2 = UserInRoom.objects.get(game_id=self.game_id, user_id=user_id2)
        self.assertEquals(user_in_room2.room_id, room2.id)

        # third user should result in the creation of a new room
        user_id3 = user_id2+1
        room3 = self.room_manager.join_room(game_id=self.game_id, user_id=user_id3)

        self.assertNotEqual(room3.id, room2.id)
        self.assertEqual(room3.num_users, 1)

        user_in_room3 = UserInRoom.objects.get(game_id=self.game_id, user_id=user_id3)
        self.assertEquals(user_in_room3.room_id, room3.id)

        # two rooms now
        self.assertEquals(len(RoomInstance.objects.all()), 2)

        # let's say first user then joins room 2
        room4 = self.room_manager.join_room(game_id=self.game_id, user_id=self.user_id, room_id=room3.id)
        self.assertEqual(room4.id, room3.id)
        self.assertEqual(room4.num_users, 2)

        user_in_room4 = UserInRoom.objects.get(game_id=self.game_id, user_id=self.user_id)
        self.assertEquals(user_in_room4.room_id, room4.id)

        # if user2 tries to join other room it should fail
        self.assertRaises(Exception, self.room_manager.join_room, game_id=self.game_id, user_id=user_id2, room_id=room3.id)

        # joins its own room => should do nothing if done AFTER the timeout period that resets the room
        time.sleep(config.ROOM_INSTANCE_TIMEOUT_SECONDS+1)

        room5 = self.room_manager.join_room(game_id=self.game_id, user_id=user_id2, room_id=room2.id)
        self.assertEquals(room5.id, room2.id)
        self.assertEquals(room5.num_users, 1)