from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from tournamentapp.models import Tournament
from announcements.models import Announcement
from .serializers import AnnouncementSerializer


class AnnouncementsListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        tournament = get_object_or_404(Tournament, slug=slug)

        if not tournament.show_announcements:
            return Response(
                {'detail': 'Announcements are not public for this tournament.'},
                status=status.HTTP_404_NOT_FOUND
            )

        announcements = Announcement.objects.filter(tournament=tournament, is_active=True)
        serializer = AnnouncementSerializer(announcements, many=True)
        return Response(serializer.data)