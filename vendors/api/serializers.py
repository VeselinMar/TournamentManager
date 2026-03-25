from rest_framework import serializers
from vendors.models import Vendor

class VendorSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = ['id', 'name', 'description', 'category', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None