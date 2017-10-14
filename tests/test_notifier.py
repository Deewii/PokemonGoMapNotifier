from notifier import Notifier, NotificationHandler
from notifier.manager import NotifierManager
import json
import unittest


class TestNotifier(unittest.TestCase):
    @staticmethod
    def _make_config(pokemons):
        return {
            "config": {
            },
            "includes": {
                "default": {
                    "pokemons": [pokemons]
                }
            },
            "notification_settings": {
                "Default": {
                    "includes": [
                        "default"
                    ],
                    "raids": [
                        "default"
                    ]
                }
            }
        }

    @staticmethod
    def _get_data(pokemon=False, encounter=False, gym_details=False, raid=False, egg=False, custom=None):
        file_name = None
        if pokemon:
            if encounter:
                file_name = "tests/data/pokemon-with-encounter.json"
            else:
                file_name = "tests/data/pokemon-without-encounter.json"
        elif gym_details:
            file_name = "tests/data/gym-details.json"
        elif raid:
            file_name = "tests/data/raid.json"
        elif egg:
            file_name = "tests/data/egg.json"
        elif custom is not None:
            file_name = "tests/data/" + custom

        with file(file_name, 'r') as fp:
            return json.load(fp)

    def setUp(self):
        config = self._make_config({"min_id": 0, "max_id": 999})
        self.notifiermanager = NotifierManager(config)
        self.config = self.notifiermanager.config
        self.notifier = self.notifiermanager.notifier
        self.notifierhandler = self.notifiermanager.handler
        self.notificationhandler = TestNotificationHandler()
        self.notifier.set_notification_handler("simple", self.notificationhandler)

    def test_pokemon_without_encounter(self):
        data = self._get_data(pokemon=True, encounter=False)

        def test(settings, pokemon):
            self.assertFalse('cp' in pokemon)
            self.assertFalse('form' in pokemon)
            self.assertFalse('attack' in pokemon)
            self.assertFalse('defense' in pokemon)
            self.assertFalse('stamina' in pokemon)
            self.assertFalse('move_1' in pokemon)
            self.assertFalse('move_2' in pokemon)
            self.assertFalse('level' in pokemon)
            self.assertFalse('iv' in pokemon)

        self.notificationhandler.on_pokemon = test
        self.notifierhandler.handle_pokemon(data['message'])

        self.assertTrue(self.notificationhandler.notify_pokemon_called)

    def test_pokemon_encounter(self):
        data = self._get_data(pokemon=True, encounter=True)

        def test(settings, pokemon):
            self.assertEqual(pokemon['cp'], 459)
            self.assertEqual(pokemon['level'], 19)
            self.assertEqual(pokemon['attack'], 8)
            self.assertEqual(pokemon['defense'], 10)
            self.assertEqual(pokemon['stamina'], 2)
            self.assertEqual(pokemon['move_1'], u'Quick Attack')
            self.assertEqual(pokemon['move_2'], u'Swift')
            self.assertAlmostEqual(pokemon['iv'], 44.44, places=2)
            self.assertFalse('form' in pokemon)

        self.notificationhandler.on_pokemon = test
        self.notifierhandler.handle_pokemon(data['message'])

        self.assertTrue(self.notificationhandler.notify_pokemon_called)

    def test_unown_encounter(self):
        data = self._get_data(custom="unown-with-encounter.json")

        def test(settings, pokemon):
            self.assertEqual(pokemon['cp'], 459)
            self.assertEqual(pokemon['level'], 19)
            self.assertEqual(pokemon['form'], 'B')

        self.notificationhandler.on_pokemon = test
        self.notifierhandler.handle_pokemon(data['message'])

        self.assertTrue(self.notificationhandler.notify_pokemon_called)

    def test_raids(self):
        data = self._get_data(raid=True)

        def test(endpoint, raid, gym):
            self.assertFalse(raid['egg'])

        self.notificationhandler.on_raid = test
        self.notifierhandler.handle_raid(data['message'])

        self.assertTrue(self.notificationhandler.notify_raid_called)

    def test_egg(self):
        data = self._get_data(egg=True)

        def test(endpoint, raid, gym):
            self.assertTrue(raid['egg'])
            self.assertFalse('move_1' in raid)
            self.assertFalse('move_2' in raid)
            self.assertFalse('id' in raid)
            self.assertFalse('cp' in raid)

        self.notificationhandler.on_egg = test
        self.notifierhandler.handle_raid(data['message'])

        self.assertTrue(self.notificationhandler.notify_egg_called)

    def test_raid_and_then_egg(self):
        egg_data = self._get_data(egg=True)['message']
        raid_data = self._get_data(raid=True)['message']

        self.assertEqual(egg_data['start'], raid_data['start'])
        self.assertEqual(egg_data['gym_id'], raid_data['gym_id'])

        def test_egg(endpoint, raid, gym):
            self.assertIsNotNone(raid)

        self.notificationhandler.on_egg = test_egg
        self.notifierhandler.handle_raid(egg_data)
        self.assertTrue(self.notificationhandler.notify_egg_called)
        self.assertFalse(self.notificationhandler.notify_raid_called)

        def test_raid(endpoint, raid, gym):
            self.assertIsNotNone(raid)

        self.notificationhandler.on_raid = test_raid
        self.notifierhandler.handle_raid(raid_data)
        self.assertTrue(self.notificationhandler.notify_raid_called)


class TestNotificationHandler(NotificationHandler):
    notify_gym_called = False
    notify_raid_called = False
    notify_egg_called = False
    notify_pokemon_called = False

    def on_gym(self, endpoint, gym):
        raise NotImplementedError("abstract method")

    def on_raid(self, endpoint, raid, gym):
        raise NotImplementedError("abstract method")

    def on_egg(self, endpoint, raid, gym):
        raise NotImplementedError("abstract method")

    def on_pokemon(self, settings, pokemon):
        raise NotImplementedError("abstract method")

    def notify_gym(self, endpoint, gym):
        self.notify_gym_called = True
        self.on_gym(endpoint, gym)

    def notify_raid(self, endpoint, raid, gym):
        self.notify_raid_called = True
        self.on_raid(endpoint, raid, gym)

    def notify_egg(self, endpoint, egg, gym):
        self.notify_egg_called = True
        self.on_egg(endpoint, egg, gym)

    def notify_pokemon(self, settings, pokemon):
        self.notify_pokemon_called = True
        self.on_pokemon(settings, pokemon)