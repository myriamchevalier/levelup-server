"""View module for handling requests about events"""
from django.core.exceptions import ValidationError
from rest_framework import status
from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from levelupapi.models import Event, Gamer, Game
from django.contrib.auth.models import User
from rest_framework.decorators import action


class EventView(ViewSet):
    """Level up events"""

    def list(self, request):
        """Handle GET requests for event resources
        
        Returns:
            Response -- JSON serialized list of events
        """
        # Get current authenticated user
        gamer = Gamer.objects.get(user=request.auth.user)
        events = Event.objects.all()

        #Set the `joined` propert on every event
        for event in events:
            #Check to see if the gamer is in the attendees list on the event
            event.joined = gamer in event.attendees.all()

        # Support filtering events by game
        game = self.request.query_params.get('gameId', None)
        if game is not None:
            events = events.filter(game__id=type)
        
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
        event = Event.objects.get(pk=pk)
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


    @action(methods=['post', 'delete'], detail=True)
    def signup(self, request, pk=None):
        """MAnaging gamers signing up for events"""
        # Django uses the `Authorization` header to determine
        # which user is making the request to sign up
        gamer = Gamer.objects.get(user=request.auth.user)

        try:
            # Handle the case if the client specifies a game
            # that doesn't exist
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response(
                {'message': 'Event does not exist.'},
                status = status.HTTP_400_BAD_REQUEST
            )
        
        # A gamer wants to sign up for an event
        if request.method == "POST":
            try:
                # Using the attendees field on the event makes it simple to add a gamer to the event
                # .add(gamer) will insert into the join table a new row the gamer_id and the event_id
                event.attendees.add(gamer)
                return Response({}, status = status.HTTP_201_CREATED)
            except Exception as ex:
                return Response({'message': ex.args[0]})
        
        # User wants to leave a previously joined event
        elif request.method == "DELETE":
            try:
                # The many to many relationship has a .remove method that removes the gamer from the attendees list
                # The method deletes the row in the join table that has the gamer_id and event_id         
                event.attendees.remove(gamer)
                return Response(None, status=status.HTTP_204_NO_CONTENT)
            except Exception as ex:
                return Response({'message': ex.args[0]})   

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
    joined = serializers.BooleanField(required=False)
    class Meta:
        model = Event
        fields = ('id', 'game', 'description', 'date', 'time', 'organizer', 'attendees', 'joined')
        depth = 1