import unittest
from django_server.models import *
import django_server.config as config
from django_server.client_packets.event import Event
import time
from api import RoomManager

class RoomAPIManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.game_id = 1
        self.user_id = 2

        self.room_manager = RoomManager()

        self.game = Game.objects.create(id=self.game_id, name='C4', max_users=2)

        config.ROOM_INSTANCE_TIMEOUT_SECONDS = 5

    def tearDown(self):
        User.objects.all().delete()
        UserMeta.objects.all().delete()
        Game.objects.all().delete()
        RoomInstance.objects.all().delete()
        UserInRoom.objects.all().delete()

    def testRoomJoin(self):

        room_packet = self.room_manager.join_room(game_id=self.game_id, user_id=self.user_id)

        self.assertIsNotNone(room_packet)

        db_room = RoomInstance.objects.get(id=room_packet.room_id)
        self.assertEquals(room_packet.room_id, db_room.id)
        self.assertEquals(room_packet.num_users, 1)
        self.assertEquals(db_room.num_users, 1)
        self.assertEquals(db_room.game_id, self.game_id)

        # should have been one event added
        self.assertEquals(len(db_room.events), 1)
        event = eval(db_room.events[0])
        self.assertEquals(event['event_id'], Event.ROOM_JOIN)
        self.assertEquals(event['user_id'], self.user_id)
        self.assertIsNone(db_room.current_user_id)
        self.assertEquals(len(db_room.user_id_order), 0)

        user_id2 = self.user_id+1
        room_packet2 = self.room_manager.join_room(game_id=self.game_id, user_id=user_id2)

        self.assertEquals(room_packet.room_id, room_packet2.room_id)

        room = RoomInstance.objects.get(id=room_packet.room_id)
        self.assertEquals(len(room.events), 2)
        self.assertEquals(len(room.user_id_order), 2)

        # was next turn data passed?
        event = eval(room.events[1])
        self.assertIn(int(event['user_id']), [self.user_id, user_id2])
        self.assertSetEqual(set(event['event_data']['user_id_order']), set([self.user_id, user_id2]))

    def testRoomTurns(self):
        room_packet = self.room_manager.join_room(game_id=self.game_id, user_id=self.user_id)

        self.assertIsNotNone(room_packet)

        db_room = RoomInstance.objects.get(id=room_packet.room_id)
        self.assertEquals(room_packet.room_id, db_room.id)
        self.assertEquals(room_packet.num_users, 1)
        self.assertEquals(db_room.num_users, 1)
        self.assertEquals(db_room.game_id, self.game_id)

        # should have been one event added
        self.assertEquals(len(db_room.events), 1)
        event = eval(db_room.events[0])
        self.assertEquals(event['event_id'], Event.ROOM_JOIN)
        self.assertEquals(event['user_id'], self.user_id)
        self.assertIsNone(db_room.current_user_id)
        self.assertEquals(len(db_room.user_id_order), 0)

        user_id2 = self.user_id+1
        room_packet2 = self.room_manager.join_room(game_id=self.game_id, user_id=user_id2)

        self.assertEquals(room_packet.room_id, room_packet2.room_id)

        room = RoomInstance.objects.get(id=room_packet.room_id)
        self.assertEquals(len(room.events), 2)
        self.assertEquals(len(room.user_id_order), 2)

        user1_event_index = 0
        user2_event_index = 0
        update_packet1 = self.room_manager.poll(game_id=self.game_id, room_id=room_packet.room_id, user_id=self.user_id, last_event_index=user1_event_index)
        update_packet2 = self.room_manager.poll(game_id=self.game_id, room_id=room_packet.room_id, user_id=user_id2, last_event_index=user2_event_index)
        user1_event_index = update_packet1.next_event_index
        user2_event_index = update_packet2.next_event_index

        # should be two events in the update_packet
        self.assertEquals(len(update_packet1.events), 2)
        self.assertEquals(len(update_packet2.events), 2)

        event = eval(update_packet1.events[1])
        self.assertEquals(event['event_id'], Event.ROOM_START)
        user_id_order = event['event_data']['user_id_order']

        event = eval(update_packet2.events[1])
        self.assertEquals(event['event_id'], Event.ROOM_START)
        user_id_order2 = event['event_data']['user_id_order']
        self.assertEquals(user_id_order, user_id_order2)

        # try to keep polling, should get nothing
        update_packet1 = self.room_manager.poll(game_id=self.game_id, room_id=room_packet.room_id, user_id=self.user_id, last_event_index=user1_event_index)
        update_packet2 = self.room_manager.poll(game_id=self.game_id, room_id=room_packet.room_id, user_id=user_id2, last_event_index=user2_event_index)

        self.assertEquals(len(update_packet1.events), 0)
        self.assertEquals(len(update_packet2.events), 0)

        # try having the wrong user start
        self.assertEquals(len(user_id_order), 2)
        first_turn_user = int(user_id_order[0])
        second_turn_user = int(user_id_order[1])

        action_id=1
        action_data=2
        self.assertRaises(Exception, self.room_manager.turn_action, game_id=self.game_id, room_id=room_packet.room_id, user_id=second_turn_user, action_id=action_id, action_data=action_data)

        # now use the right user
        self.room_manager.turn_action(game_id=self.game_id, room_id=room_packet.room_id, user_id=first_turn_user, action_id=action_id, action_data=action_data)

        room = RoomInstance.objects.get(id=room_packet.room_id)
        self.assertEquals(len(room.events), 3)
        self.assertEquals(room.current_user_id, second_turn_user)

        action_id2 = action_id+1
        action_data2 = action_data+1
        self.room_manager.turn_action(game_id=self.game_id, room_id=room_packet.room_id, user_id=second_turn_user, action_id=action_id2, action_data=action_data2)

        room = RoomInstance.objects.get(id=room_packet.room_id)
        self.assertEquals(len(room.events), 4)
        self.assertEquals(room.current_user_id, first_turn_user)

        update_packet1 = self.room_manager.poll(game_id=self.game_id, room_id=room_packet.room_id, user_id=self.user_id, last_event_index=user1_event_index)
        update_packet2 = self.room_manager.poll(game_id=self.game_id, room_id=room_packet.room_id, user_id=user_id2, last_event_index=user2_event_index)
        user1_event_index = update_packet1.next_event_index
        user2_event_index = update_packet2.next_event_index

        self.assertEquals(len(update_packet1.events), 2)
        self.assertEquals(len(update_packet2.events), 2)

        # make sure we received the action turn data
        event = eval(update_packet1.events[0])
        self.assertEquals(event['event_id'], Event.TURN_ACTION)
        self.assertEquals(event['user_id'], first_turn_user)
        self.assertEquals(event['event_data']['action_id'], action_id)
        self.assertEquals(event['event_data']['action_data'], action_data)

        event = eval(update_packet2.events[1])
        self.assertEquals(event['event_id'], Event.TURN_ACTION)
        self.assertEquals(event['user_id'], second_turn_user)
        self.assertEquals(event['event_data']['action_id'], action_id2)
        self.assertEquals(event['event_data']['action_data'], action_data2)