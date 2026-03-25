from rest_framework import serializers
from announcements.models import Announcement

class AnnouncementSerializer(serializers.ModelSerializer):

    class Meta:
        model=Announcement
        fields=['message', 'starts_at', 'ends_at', 'is_active', 'created_at']