# from django.shortcuts import render
# from django.http import HttpResponse
import requests, string
import urllib.parse
from rest_framework import permissions, serializers, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response 
from .models import *
from django.db.models import Q
from .serializer import (PaperSerializer, AuthorSerializer, PaperListSerializer,
                         AffiliationSerializer, PaperAuthorAffiliationSerializer)


class AutoComplete(APIView):
    """
        GET Rest API view for send request to graph database manager
        to get autocompletion.
    """
    
    # TODO: change from local to production url
    # autocomplete_url = "https://localhost:5000/complete?q={keywords}"
    autocomplete_url = "http://35.247.162.211/complete"

    def get(self, request, format=None):
        payload = urllib.parse.urlencode({"q" : self.request.GET.get('keywords', '')})
        response = requests.get(self.autocomplete_url,params=payload)
        ret = [
            {"value": k, "label": k} for k in response.json()['sentences']
        ]
        return Response(ret,status=status.HTTP_200_OK)

class GraphGet(APIView):
    """
        GET Rest API view for send request to graph database manager
        to get graph
    """

    # TODO: change from local to production url
    graph_url = "http://35.247.162.211/graph"

    def get(self, request, format=None):
        payload = urllib.parse.urlencode({
            "keyword": self.request.GET.get('keyword', ''),
            "paper_title": self.request.GET.get('paper_title', ''),
            "limit": self.request.GET.get('limit', 0)
        })
        # print(payload)
        response = requests.get(self.graph_url,params=payload)
        relations = response.json().get('graph', [])
        nodes = set()
        links = list()
        for relation in relations:
            relation_name, ent_1, ent_2 = relation
            ent_1, ent_2 = tuple(ent_1), tuple(ent_2)
            nodes.update([ent_1[0], ent_2[0]])
            links.append({
                'source': ent_1[0],
                'target': ent_2[0],
                'label': relation_name,
            })
        nodes = [{'id': name} for name in nodes]
        data = {'nodes': nodes, 'links': links}
        return Response(data,status=status.HTTP_200_OK)

class PaperD3Get(APIView):
    """
    API for retrieving data to visualize w/ D3 force graph
    """
    
    graph_url = "http://35.247.162.211/graph"

    def get(self, request, format=None):
        paper_id = self.request.GET.get('paper_id')
        paper_title = Paper.objects.get(pk=paper_id).paper_title
        payload = urllib.parse.urlencode({
            "paper_title": paper_title,
            "limit": self.request.GET.get('limit', 0)
        })
        # print(payload)
        response = requests.get(self.graph_url,params=payload)
        relations = response.json().get('graph', [])
        
        ent_id = 1
        nodes = dict()
        links = list()
        
        for relation in relations:
            relation_name, ent_1, ent_2 = relation
            ent_1, ent_2 = tuple(ent_1), tuple(ent_2)
            
            if ent_1 not in nodes:
                nodes[ent_1] = ent_id; ent_id += 1
            if ent_2 not in nodes:
                nodes[ent_2] = ent_id; ent_id += 1

            links.append({
                'source': nodes[ent_1],
                'target': nodes[ent_2],
                'label': relation_name,
            })

        node_list = []
        for (ent, eid) in nodes.items():
            ent_name, ent_label = ent
            node_list.append({
                'id': eid,
                'name': ent_name,
                'labels': ent_label
            })
        data = {'nodes': node_list, 'links': links}
        return Response(data,status=status.HTTP_200_OK)
        
class PaperGet(generics.RetrieveAPIView):
    """
    GET Rest API view for requesting individual paper information.
    Mainly used on Paper page
    """

    serializer_class = PaperSerializer
    
    def get_object(self):
        try:
            obj = Paper.objects.prefetch_related('paperauthoraffiliation_set')\
                            .get(pk=self.request.GET.get('paper_id', None))
        except Paper.DoesNotExist:
            return None
        return obj
    
class PaperList(generics.ListAPIView):
    """
    GET Rest API view for requesting papers information.
    """

    # TODO: adding explanation retrieving from graph manager to response 
    explanation_url = 'http://35.247.162.211/explain'

    def _get_paper_by_ids(self, paper_ids):
        return Paper.objects.prefetch_related('paperauthoraffiliation_set').filter(
                paper_id__in=paper_ids)
    
    def get_queryset(self):
        """
        Return the queryset for retrieving papers information
        """
        paper_ids = self.request.GET.get('paper_ids', None)

        if paper_ids:
            paper_ids = [int(i) for i in paper_ids.split(',')]
            return self._get_paper_by_ids(paper_ids)
    
    def list(self, request, *args, **kwargs):
        papers = self.get_queryset()
        capitalizer = lambda x: string.capwords(x)
        try:
            serializer = PaperListSerializer(instance=papers,many=True)
            response_data = serializer.data
            paper_titles = []
            abstracts = []
            for paper in response_data:
                paper['conference'] = capitalizer(paper['conference'])
                paper['authors'] = list(map(capitalizer, paper['authors']))
                paper['affiliations'] = list(map(capitalizer, paper['affiliations']))
                paper_titles.append(paper['paper_title'])
                abstracts.append(paper['abstract'])

            no_ex = request.GET.get('no_ex', '')
            
            if no_ex == '':
                explanations = requests.post(self.explanation_url, json={
                    'keyword': request.GET.get('keywords', None),
                    'papers': paper_titles,
                    'abstracts': abstracts,
                })
                
                explanation_json = explanations.json()['explanations']
                for i, paper in enumerate(response_data):
                    paper['explanation'] = explanation_json[i]

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)

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

    params = {
        'q' : <str> keyword(s)
        'lim': <int> limit of paper
        'skip': <int> skip to start at
        'sortBy': <int> sort algorithms
            - 0 -> relevance
            - 1 -> citation count
            - 2 -> date
        'sortOrder': <int> sort order
            - 0 -> best first (most popular,citation count, newest)
            - 1 -> opposite to best first
    }

    """

    preprocess_url = "http://35.247.162.211/preprocess"

    def _get_keys(self, obj):
        LIMIT = 1
        keywords = []
        res = {}
        for key in obj.keys():
            if key not in res.keys():
                res[key] = []
            for i in range(LIMIT):
                keywords.append(key)
                if i < len(obj[key]):
                    keywords.append(obj[key][i])
                    res[key].append(obj[key][i])
        return keywords,res


    def _get_papers(self, keywords):
        mapping_keyword_id = {}
        papers = []
        for keyword in keywords:

            # regx
            regx = r'\b{}(s|es){{0,1}}\b'.format(keyword)
            temp_papers = Paper.objects.filter(
                Q(abstract__iregex=regx) | Q(paper_title__iregex=regx)
            )

            # # contains
            # temp_papers = Paper.objects.filter(
            #     Q(abstract__icontains=keyword) | Q(paper_title__icontains=keyword)
            # )

            mapping_keyword_id[keyword] = [paper.paper_id for paper in temp_papers]
            papers += temp_papers
        return list(set(papers)),mapping_keyword_id


    def get(self, request, format=None):
        """
        Return ranked search result 
        """
        q = request.GET.get('q', '')
        limit = int(request.GET.get('lim',10))
        skip = int(request.GET.get('skip', 0))
        sort_by = int(request.GET.get('sortBy',0))
        sort_order = int(request.GET.get('sortOrder',0))
        response = requests.post(self.preprocess_url,json={"text": q})
        # TODO: improve ranking algorithm
        keywords,cleaned_response = self._get_keys(response.json())
        papers,mapping_keyword_id = self._get_papers(keywords)
        

        papers_score = {}
        temp_scores = []

        #score from keyword(s) included
        for i,paper in enumerate(papers):
            n_keyword = 0
            for keyword in cleaned_response.keys():
                if paper.paper_id in mapping_keyword_id[keyword]:
                    n_keyword += 1
                else:
                    for semantic_keyword in cleaned_response[keyword]:
                        if paper.paper_id in mapping_keyword_id[semantic_keyword]:
                            n_keyword += 1
                            break
            temp_scores.append([paper.paper_id,n_keyword,0])
        
        #sort_by
        #score from popularity -> normailized in range [0,100]
        if(sort_by == 0):
            for i,paper in enumerate(papers):
                temp_scores[i][2] = paper.popularity
        elif(sort_by == 1):
            for i,paper in enumerate(papers):
                temp_scores[i][2] = paper.citation_count
        elif(sort_by == 2):
            for i,paper in enumerate(papers):
                temp_scores[i][2] = paper.publish_date

        #final_score
        for score in temp_scores:
            papers_score[score[0]] = (score[1],score[2])
        
        #sort keyword score first, then other score
        if(sort_order == 0):
            sorted_papers = [paper_id for paper_id in dict(sorted(papers_score.items(), key=lambda score: (score[1][0],score[1][1]))[::-1]).keys()]
        else:
            sorted_papers = [paper_id for paper_id in dict(sorted(papers_score.items(), key=lambda score: (-score[1][0],score[1][1]))).keys()]

        print(sorted(papers_score.items(), key=lambda score: (score[1][0],score[1][1]))[::-1])
        return Response(sorted_papers[skip:skip+limit], status=status.HTTP_200_OK)
