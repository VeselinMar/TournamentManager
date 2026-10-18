from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from tournamentapp.api.caching import cached_response

from tournamentapp.models import Tournament
from programme.models import SideEvent
from .serializers import SideEventSerializer


class SideEventListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        tournament = get_object_or_404(Tournament, slug=slug)

        if not tournament.show_side_events:
            return Response(
                {'detail': 'Side Events are not public for this tournament.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return cached_response(
            request, tournament, "side-events",
            lambda: SideEventSerializer(SideEvent.objects.filter(tournament=tournament, is_active=True), many=True).data,
        )