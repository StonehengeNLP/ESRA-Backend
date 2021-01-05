from django.db.models import fields
from django.db.models.base import Model
from rest_framework.fields import Field, SerializerMethodField
from rest_framework.serializers import ModelSerializer
from .models import *


class AffiliationSerializer(ModelSerializer):
    """
    Serializer for retrieveing/adding affiliation information
    """
    class Meta:
        model = Affiliation
        fields = "__all__"
        extra_kwargs = {
        }
    
    def create(self, validated_data):
        instance, created = self.Meta.model.objects.get_or_create(**validated_data)
        return instance

class AuthorSerializer(ModelSerializer):
    """
    Serializer for retrieving/adding author information
    """
    class Meta:
        model = Author
        fields = "__all__"
        extra_kwargs = {
        }
    
    def create(self, validated_data):
        instance, created = self.Meta.model.objects.get_or_create(**validated_data)
        return instance 

class PaperAuthorAffiliationSerializer(ModelSerializer):
    
    author_info = AuthorSerializer(source='author',many=False, read_only=True)
    affiliation_info = AffiliationSerializer(source='affiliation', many=False, read_only=True)

    class Meta:
        model = PaperAuthorAffiliation
        raad_only_fields = ('author_info', 'affiliation_info', )
        fields = ('paper', 'author', 'affiliation', 'author_info', 
                  'affiliation_info', )
        extra_kwargs = {
            'paper': {'write_only': True},
            'author': {'write_only': True},
            'affiliation': {'write_only': True},
        }


class PaperSerializer(ModelSerializer):
    """
    Serializer for retrieving individual paper information
    """

    paper_authors = PaperAuthorAffiliationSerializer(
        source='paperauthoraffiliation_set', 
        many=True, 
        read_only=True
    )
    cited_by = SerializerMethodField()

    class Meta:
        model = Paper
        fields = '__all__'
        read_only_fields = ('paper_id', 'paper_authors',)
        extra_kwargs = {
        }

    def get_cited_by(self, obj):
        return Paper.cite_to.through.objects.filter(to_paper_id=obj.paper_id) \
                                            .values_list('from_paper_id', flat=True)

class PaperListSerializer(ModelSerializer):
    """
    Serializer uses for retrieveing paper information list only, do not use for
    creating new paper
    """

    authors = SerializerMethodField()
    affiliations = SerializerMethodField()

    class Meta:
        model = Paper
        fields = ('paper_id', 'paper_title', 'conference', 'abstract', 
                  'authors', 'affiliations', )
    
    def get_authors(self, obj):
        return obj.paperauthoraffiliation_set.all().values_list(
            'author__author_name', flat=True
        )

    def get_affiliations(self, obj):
        return obj.paperauthoraffiliation_set.all().values_list(
            'affiliation__affiliation_name', flat=True
        )

