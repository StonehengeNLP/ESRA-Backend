from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import permissions, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response 
from .models import *

# Create your views here.
def index(request):
    return HttpResponse("Hello, world. You're at the esra backend site.")

class GetPaper(generics.RetrieveAPIView):

    def get_paper(self):
        result_object = {}
        paper = Paper.objects.get(pk=self.request.data['paper_id'])

        #handle author
        writes = WriteEntity.objects.filter(paper_id=self.request.data['paper_id']) #list of writer object
        authors = []
        for write in writes:
            authors.append(Author.objects.get(author_id=write.author_id)) #list of authors

        #handle affiliation
        affiliations = []
        for author in authors:
            temp_affs = Affiliation.objects.filter(author_id=author.author_id)
            for temp_aff in temp_affs:
                affiliations.append(temp_aff)

        # create return object
        result_object['paper_id'] = self.request.data['paper_id']
        result_object['paper_title'] = paper.paper_title
        result_object['conference'] = paper.conference
        result_object['arxiv_id'] = paper.arxiv_id
        result_object['mag_id'] = paper.mag_id
        result_object['citation_count'] = paper.citation_count
        result_object['publish_date'] = paper.publish_date
        
        result_authors = []
        for author in authors:
            temp_author = {}
            temp_author['author_name'] = author.author_name
            temp_aff = []
            for affiliation in affiliations:
                if affiliation.author_id == author.author_id:
                    temp_aff.append(affiliation.affiliation_name)
            temp_author['affiliations'] = temp_aff
            result_authors.append(temp_author)
        result_object['authors'] = result_authors

        return result_object

    def get(self, request, *args, **kargs):
        try:
            paper_obj = self.get_paper()
        except:
            return Response("Paper doesn't not exist.",status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(paper_obj, status=status.HTTP_200_OK)

        

        


