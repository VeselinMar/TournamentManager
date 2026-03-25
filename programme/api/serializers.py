from rest_framework import serializers
from programme.models import SideEvent

class SideEventSerializer(serializers.ModelSerializer):

    class Meta:
        model=SideEvent
        fields=['name', 'description', 'start_time', 'end_time', 'is_active']