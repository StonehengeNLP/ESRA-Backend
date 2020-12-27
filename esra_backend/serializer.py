from django.db.models.base import Model
from rest_framework.fields import Field
from rest_framework.serializers import ModelSerializer, Serializer
from .models import *

class AffiliationSerializer(ModelSerializer):

    class Meta:
        model = Affiliation
        fields = '__all__'
        extra_kwargs = {
            'author': {'write_only': True},
        }

class AuthorSerializer(ModelSerializer):

    author_affiliations = AffiliationSerializer(source='affiliation_set',
                                                many=True, read_only=True)

    class Meta:
        model = Author
        fields = '__all__'
        extra_kwargs = {
            'paper': {'write_only': True},
        }


class PaperSerializer(ModelSerializer):

    paper_authors = AuthorSerializer(source='author_set', many=True, 
                                     read_only=True)

    class Meta:
        model = Paper
        fields = '__all__'