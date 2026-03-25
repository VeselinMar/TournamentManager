from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from tournamentapp.models import Tournament
from vendors.models import Vendor
from .serializers import VendorSerializer


class VendorListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        tournament = get_object_or_404(Tournament, slug=slug)

        if not tournament.show_vendors:
            return Response(
                {'detail': 'Vendors are not public for this tournament.'},
                status=status.HTTP_404_NOT_FOUND
            )

        vendors = Vendor.objects.filter(tournament=tournament, is_active=True)
        serializer = VendorSerializer(vendors, many=True)
        return Response(serializer.data)