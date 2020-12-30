from django.db.models import fields
from django.db.models.base import Model
from rest_framework.fields import Field, SerializerMethodField
from rest_framework.serializers import ModelSerializer
from .models import *


class AffiliationSerializer(ModelSerializer):

    class Meta:
        model = Affiliation
        fields = "__all__"
        extra_kwargs = {
        }
    
    def create(self, validated_data):
        instance, created = self.Meta.model.objects.get_or_create(**validated_data)
        return instance

class AuthorSerializer(ModelSerializer):

    class Meta:
        model = Author
        fields = "__all__"
        extra_kwargs = {
        }
    
    def create(self, validated_data):
        instance, created = self.Meta.model.objects.get_or_create(**validated_data)
        return instance 

class PaperAuthorAffiliationSerializer(ModelSerializer):
    
    author = AuthorSerializer(many=False, read_only=True)
    affiliation = AffiliationSerializer(many=False, read_only=True)

    class Meta:
        model = PaperAuthorAffiliation
        fields = "__all__"

class PaperSerializer(ModelSerializer):

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