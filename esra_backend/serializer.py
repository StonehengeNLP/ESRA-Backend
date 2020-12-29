from django.db.models import fields
from django.db.models.base import Model
from rest_framework.fields import Field, SerializerMethodField
from rest_framework.serializers import ModelSerializer
from .models import *


class AffiliationSerializer(ModelSerializer):

    class Meta:
        model = Affiliation
        fields = ('affiliation_name', 'author')
        extra_kwargs = {
            'author': {'write_only': True},
        }
    
    def create(self, validated_data):
        affiliation_name = validated_data['affiliation_name']
        instance = self.Meta.model.object.get_or_create(**validated_data)
        return instance

class AuthorSerializer(ModelSerializer):

    author_affiliations = AffiliationSerializer(source='affiliation_set',
                                                many=True)

    class Meta:
        model = Author
        fields = ('author_name', 'author_affiliations', 'paper')
        extra_kwargs = {
            'paper': {'write_only': True},
        }
    
    def create(self, validated_data):
        author_name = validated_data['author_name']
        affiliation = validated_data.pop('affiliation')
        instance = self.Meta.model.object.get_or_create(**validated_data)
        return instance 

class PaperSerializer(ModelSerializer):

    paper_authors = AuthorSerializer(source='author_set', many=True, 
                                     read_only=True)
    cited_by = SerializerMethodField()

    class Meta:
        model = Paper
        fields = '__all__'
        read_only_fields = ('paper_id', 'paper_authors',)
        extra_kwargs = {
            # 'paper_id': {'read_only': True},
        }

    def get_cited_by(self, obj):
        return Paper.cite_to.through.objects.filter(to_paper_id=obj.paper_id) \
                                            .values_list('from_paper_id', flat=True)