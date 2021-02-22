from django.db.models import fields
from django.db.models.base import Model
from rest_framework.fields import Field, SerializerMethodField
from rest_framework.serializers import ModelSerializer
from .models import *


# class AffiliationSerializer(ModelSerializer):
#     """
#     Serializer for retrieveing/adding affiliation information
#     """
#     class Meta:
#         model = Affiliation
#         fields = "__all__"
#         extra_kwargs = {
#         }
    
#     def create(self, validated_data):
#         instance, created = self.Meta.model.objects.get_or_create(**validated_data)
#         return instance

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

class PaperAuthorSerializer(ModelSerializer):
    
    author_info = AuthorSerializer(source='author',many=False, read_only=True)

    class Meta:
        model = PaperAuthor
        raad_only_fields = ('author_info', )
        fields = ('paper', 'author', 'author_info', )
        extra_kwargs = {
            'paper': {'write_only': True},
            'author': {'write_only': True},
        }

# class PaperAuthorAffiliationSerializer(ModelSerializer):
    
#     author_info = AuthorSerializer(source='author',many=False, read_only=True)
#     affiliation_info = AffiliationSerializer(source='affiliation', many=False, read_only=True)

#     class Meta:
#         model = PaperAuthorAffiliation
#         raad_only_fields = ('author_info', 'affiliation_info', )
#         fields = ('paper', 'author', 'affiliation', 'author_info', 
#                   'affiliation_info', )
#         extra_kwargs = {
#             'paper': {'write_only': True},
#             'author': {'write_only': True},
#             'affiliation': {'write_only': True},
#         }


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
                  'authors', )
    
    def get_authors(self, obj):
        return obj.paperauthoraffiliation_set.all().values_list(
            'author__author_name', flat=True
        )

    # def get_affiliations(self, obj):
    #     return obj.paperauthoraffiliation_set.all().values_list(
    #         'affiliation__affiliation_name', flat=True
    #     )

class PaperSerializer(PaperListSerializer):
    """
    Serializer for retrieving individual paper information
    """
    cited_by = SerializerMethodField()

    class Meta(PaperListSerializer.Meta):
        model = Paper
        fields = PaperListSerializer.Meta.fields + ('cite_to', 'cited_by', 'citation_count')
        extra_kwargs = {}

    def get_cited_by(self, obj):
        return Paper.cite_to.through.objects.filter(to_paper_id=obj.paper_id) \
                                            .values_list('from_paper_id', flat=True)