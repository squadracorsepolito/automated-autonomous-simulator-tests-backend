# auto_tests/serializers.py
from rest_framework import serializers
from .models import Rosbags

class RosbagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rosbags
        fields = '__all__'  # tutti i campi del modello
