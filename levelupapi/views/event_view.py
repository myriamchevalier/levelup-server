"""View module for handling requests about events"""
from django.core.exceptions import ValidationError
from rest_framework import status
from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from levelupapi.models import Event, Gamer, Game
from django.contrib.auth.models import User



class EventView(ViewSet):
    """Level up events"""

    def list(self, request):
        """Handle GET requests for event resources
        
        Returns:
            Response -- JSON serialized list of events
        """
        events = Event.objects.all()

        serializer = EventSerializer(
            events, many=True, context = {'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Handle GET requests for a single event
        
        Returns:
            Response -- JSON serialized event instance
        """
        # Use try and except in case requested pk doesn't exist
        try:
            event = Event.objects.get(pk=pk)
            serializer = EventSerializer(event, context = {'request':request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def create(self, request):
        """Handle POST operations

        Returns:
            Response -- JSON serialized event instance
        """
        organizer = Gamer.objects.get(user=request.auth.user)
        game = Game.objects.get(pk=request.data['gameId'])

        try:
            # Create a new Python instance of the Event class
            # and set its properties from what was sent in the
            # body of the request from the client.
            event = Event.objects.create(
                game = game,
                description = request.data["description"],
                date = request.data["date"],
                time = request.data["time"],
                organizer = organizer
            )
            serializer = EventSerializer(event, context={'request':request})
            return Response(serializer.data)
        
        # If anything went wrong, catch the exception and
        # send a response with a 400 status code to tell the
        # client that something was wrong with its request data
        except ValidationError as ex:
            return Response({"reason": ex.message}, status=status.HTTP_400_BAD_REQUEST)

    def  update(self, request, pk=None):
        """Handle PUT requests for an event
        
        Returns:
            Response -- Empty body with 204 status code
        """
        organizer = Gamer.objects.get(user=request.auth.user)
        game = Game.objects.get(pk=request.data['gameId'])

        # Do mostly the same thing as POST(create), but instead of
        # creating a new instance of Event, get the event record
        # from the database whose primary key is `pk`
        event = Game.objects.get(pk=pk)
        event.game = game
        event.description = request.data['description']
        event.date = request.data['date']
        event.time = request.data['time']
        event.organizer = organizer

        event.save()

        # 204 status code means everything worked but the
        # server is not sending back any data in the response
        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):
        """Handle DELETE requests for a single event

        Returns:
            Response -- 200, 404, or 500 status code
        """
        try:
            event = Event.objects.get(pk=pk)
            event.delete()

            return Response({}, status=status.HTTP_204_NO_CONTENT)

        except Event.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

        except Exception as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EventGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ('id', 'title', 'maker', 'number_of_players', 'skill_level', 'game_type')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')
class OrganizerGamerSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Gamer
        fields = ('id', 'user')


class EventSerializer(serializers.ModelSerializer):
    """JSON serializer for events
    
    Arguments:
        serializer type
    """
    organizer = OrganizerGamerSerializer()
    class Meta:
        model = Event
        fields = ('id', 'game', 'description', 'date', 'time', 'organizer')
        depth = 1