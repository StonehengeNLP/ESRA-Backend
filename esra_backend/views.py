# from django.shortcuts import render
# from django.http import HttpResponse
import requests
import json
from rest_framework import permissions, serializers, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response 
from .models import *
from django.db.models import Q
from .serializer import (PaperSerializer, AuthorSerializer, 
                         AffiliationSerializer, PaperAuthorAffiliationSerializer)


class AutoComplete(APIView):
    """
        GET Rest API view for send request to graph database manager
        to get autocompletion.
    """
    
    # TODO: change from local to production url
    autocomplete_url = "http://localhost:5000/complete?q={keywords}"

    def get(self, request, format=None):
        keywords = self.request.GET.get('keywords', '').replace(' ','%20')
        response = requests.get(self.autocomplete_url.format(keywords=keywords))
        ret = [
            {"value": k, "label": k} for k in response.json()['sentences']
        ]
        return Response(ret,status=status.HTTP_200_OK)
        
class PaperGet(generics.RetrieveAPIView):
    """
    GET Rest API view for requesting individual paper information.
    Mainly used on Paper page
    """

    serializer_class = PaperSerializer
    
    def get_object(self):
        obj = Paper.objects.prefetch_related('paperauthoraffiliation_set')\
                           .get(pk=self.request.data['paper_id'])
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

class PaperPost(generics.CreateAPIView):
    """
    Post Rest API for adding new paper
    """

    def post(self, request, *args, **kwargs):
        serializer = PaperSerializer(data=request.data,
                                     many=isinstance(request.data, list))
        if serializer.is_valid():
            paper = serializer.save()
            if paper:
                json = serializer.data
                return Response(json, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AuthorPost(generics.CreateAPIView):
    """
    Post Rest API for adding new author
    """

    def post(self, request, *args, **kwargs):
        serializer = AuthorSerializer(data=request.data,
                                      many=isinstance(request.data, list))
        if serializer.is_valid():
            author = serializer.save()
            if author:
                json = serializer.data
                return Response(json, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AffiliationPost(generics.CreateAPIView):
    """
    Post Rest API for adding new affiliation
    """

    def post(self, request, *args, **kwargs):
        serializer = AffiliationSerializer(data=request.data, 
                                           many=isinstance(request.data, list))
        if serializer.is_valid():
            affiliation = serializer.save()
            if affiliation:
                json = serializer.data
                return Response(json, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PaperPatch(generics.UpdateAPIView):
    """
    Patch Rest API for update paper relation
    """

    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

class PaperAuthorAffilationPost(generics.CreateAPIView):
    """
    Post Rest API for adding paper-author-affiliation relations
    """

    def post(self, request, *args, **kwargs):
        serializer = PaperAuthorAffiliationSerializer(data=request.data, 
                                           many=isinstance(request.data, list))
        if serializer.is_valid():
            affiliation = serializer.save()
            if affiliation:
                json = serializer.data
                return Response(json, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SearchGet(APIView):
    """
    Simple Rest API view for retrieving search result
    """

    def _get_keys(self, obj):
        LIMIT = 1
        keywords = []
        for key in obj.keys():
            keywords.append(key)
            for i in range(LIMIT):
                if i < len(obj[key]):
                    keywords.append(obj[key][i])
        return keywords

    def _get_papers(self, keywords):
        papers = []
        for keyword in keywords:
            temp_papers = Paper.objects.filter(Q(abstract__icontains=keyword) | Q(paper_title__icontains=keyword))
            papers += temp_papers
        return list(set(papers))

    def get(self, request, format=None):
        """
        Return ranked search result 
        """
        q = request.data['q']
        limit = request.data.get('lim',5)
        skip = request.data.get('skip', 0)
        response = requests.post("http://localhost:5000/preprocess",json={"text": q})

        # TODO: improve ranking algorithm
        keywords = self._get_keys(response.json())
        papers = self._get_papers(keywords)
        papers = sorted(papers, key=lambda x: x.popularity, reverse=True)
        papers = [paper.paper_id for paper in papers]
        return Response(papers[skip:skip+limit], status=status.HTTP_200_OK)
