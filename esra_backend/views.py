from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import permissions, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response 
from .models import *
from .serializer import PaperSerializer
from django.core.exceptions import ImproperlyConfigured


class PaperGet(generics.ListAPIView):
    """
    GET Rest API view for requesting papers information.
    """

    serializer_class = PaperSerializer

    def get_queryset(self):
        """
        This view should return a list of all the papers
        This will requires JSON body contains list of 'paper_ids' 
        
        :return: [ paper_object_1, ... , paper_object_n ]
        """
        paper_ids = self.request.data['paper_ids']
        return Paper.objects.prefetch_related('author_set', 'author_set__affiliation_set').filter(
            paper_id__in=paper_ids)