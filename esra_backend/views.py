# from django.shortcuts import render
# from django.http import HttpResponse
from rest_framework import permissions, status, generics
# from rest_framework.views import APIView
# from rest_framework.response import Response 
from .models import *
from .serializer import PaperSerializer


class PaperGet(generics.RetrieveAPIView):
    """
    GET Rest API view for requesting individual paper information.
    Mainly used on Paper page
    """

    serializer_class = PaperSerializer
    
    def get_object(self):
        obj = Paper.objects.prefetch_related('author_set').get(pk=self.request.data['paper_id'])
        return obj
    
class PaperList(generics.ListAPIView):
    """
    GET Rest API view for requesting papers information.
    """

    serializer_class = PaperSerializer

    def _get_paper_by_ids(self, paper_ids):
        return Paper.objects.prefetch_related('author_set', 'author_set__affiliation_set').filter(
                paper_id__in=paper_ids)
    
    def get_queryset(self):
        """
        This view should return a list of all the papers
        This will requires JSON body contains 'keywords' 
        
        :param keywords: text to be searched
        :return: [ paper_object_1, ... , paper_object_n ]
        """
        keywords = self.request.data.get('keywords', None)
        
        if keywords:
            # TODO: find papers using given keywords
            paper_ids = [1]
            return self._get_paper_by_ids(paper_ids)