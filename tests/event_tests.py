from django.http import response
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from levelupapi.models import GameType, Game, Event, game_type

class EventTests(APITestCase):
    def setUp(self):
        """
        Create a new Gamer, collect the auth Token, and create a sample GameType
        """

        # URL path for registering
        url = '/register'

        # Gamer properties
        gamer = {
            "username": "steve",
            "password": "Admin8*",
            "email": "steve@stevebrownlee.com",
            "address": "100 Infinity Way",
            "phone_number": "555-1212",
            "first_name": "Steve",
            "last_name": "Brownlee",
            "bio": "Love those gamez!!"
        }

        # Initiate POST request and capture the response
        response = self.client.post(url, gamer, format='json')

        # Store the TOKEN from response data
        self.token = Token.objects.get(pk=response.data['token'])

        # Use the TOKEN to authenticate the requests

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Assert that the response status code is 201 (CREATED)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # SEED THE DATABASE WITH A GAMETYPE
        game_type = GameType()
        game_type.label = "Board game"

        game_type.save()

        self.game = Game.objects.create(
            game_type=game_type,
            title="Monopoly",
            maker="Hasbro",
            gamer_id=1,
            number_of_players=5,
            skill_level=2
        )

    def test_create_event(self):
        """
        Ensure we can POST a new event
        """ 

        # Define the URL path for creating new event
        url = '/events'

        # Define the event properties

        event = {
            "date": "2021-12-23",
            "time": "12:30:00",
            "description": "Game Day",
            "gameId": self.game.id
        }

        # Initiate POST request and capture response

        response = self.client.post(url, event, format='json')

        # Assert that the response status code is 201(CREATED)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert that the values are correct
        self.assertIsNotNone(response.data['id'])
        self.assertEqual(response.data['date'], event['date'])
        self.assertEqual(response.data['time'], event['time'])
        self.assertEqual(response.data['description'], event['description'])
        self.assertEqual(response.data['game']['id'],event['gameId'])
        self.assertEqual(response.data['organizer']['id'], 1)


    def test_get_event(self):
        """
        Ensure we can GET an existing event
        """

        # Create new instance of Event
        event = Event()
        event.organizer_id = 1
        event.date = "2021-12-20"
        event.time = "11:00:00"
        event.description = "Playing Azul"
        event.game_id = 1

        event.save()

        url = f'/events/{event.id}'

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['date'], event.date)
        self.assertEqual(response.data['time'], event.time)
        self.assertEqual(response.data['description'], event.description)
        self.assertEqual(response.data['organizer']['id'], event.organizer_id)
        self.assertEqual(response.data['game']['id'], event.game_id)



        