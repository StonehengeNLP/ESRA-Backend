# from django.shortcuts import render
# from django.http import HttpResponse
from numpy.lib.utils import source
import requests, string
import urllib.parse
from rest_framework import permissions, serializers, status, generics
from rest_framework import response
from rest_framework.views import APIView
from rest_framework.response import Response 
from .models import *
from django.db.models import Q
# from rank_bm25 import BM25Okapi
from .serializer import (PaperSerializer, AuthorSerializer, PaperListSerializer,
                         AffiliationSerializer, PaperAuthorAffiliationSerializer)
from time import sleep
import os
from django.conf import settings
import pickle
from sentence_transformers import SentenceTransformer
import scipy
# from .data import embedding_vector

GM_URL = os.environ.get('GM_URL')

from .documents import PaperDocument
from .helps import (ElasticSearchPaperAndService,
                    ElasticSearchPaperFilterAndService, 
                    ElasticSearchPaperOrService,
                    ElasticSearchPaperFilterOrService,
                    ElasticSearchPaperPhraseService,
                    ElasticSearchPaperFilterPhraseService)
from .utils import rebuild_elasticsearch_index, delete_elasticsearch_index, is_empty_or_null
import elasticsearch
import datetime


class AutoComplete(APIView):
    """
        GET Rest API view for send request to graph database manager
        to get autocompletion.
    """
    
    # TODO: change from local to production url
    # autocomplete_url = "https://localhost:5000/complete?q={keywords}"
    autocomplete_url = f"{GM_URL}/complete"

    def get(self, request, format=None):
        payload = urllib.parse.urlencode({"q" : self.request.GET.get('keywords', '')})
        response = requests.get(self.autocomplete_url,params=payload)
        ret = [
            {"value": k, "label": k} for k in response.json()['sentences']
        ]
        return Response(ret,status=status.HTTP_200_OK)

class PaperD3Get(APIView):
    """
    API for retrieving data to visualize w/ D3 force graph
    """
    
    graph_url = f"{GM_URL}/graph"

    def get(self, request, format=None):
        paper_id = self.request.GET.get('paper_id')
        paper_title = Paper.objects.get(pk=paper_id).paper_title
        authors = Paper.objects.get(pk=paper_id).paperauthoraffiliation_set\
                               .values_list('author__author_name', flat=True)
        authors = list(dict.fromkeys(authors))
        payload = urllib.parse.urlencode({
            "paper_title": paper_title,
            "limit": self.request.GET.get('limit', 0)
        })
        response = requests.get(self.graph_url,params=payload)
        relations = response.json().get('graph', [])
        if relations==[]:
            data = {'nodes': [], 'links': []}
            return Response(data,status=status.HTTP_200_OK)


        ent_id = 1
        link_id = 1
        nodes = dict()
        links = list()
        link_nums = dict()
        paper_end_id = -1
        found_paper = False
        for relation in relations:
            relation_name, ent_1, ent_2 = relation
            ent_1, ent_2 = tuple(ent_1), tuple(ent_2)
            
            if ent_1 not in nodes:
                nodes[ent_1] = ent_id
                if not found_paper and ent_1[1] == 'Paper':
                    paper_end_id = ent_id
                ent_id += 1
            if ent_2 not in nodes:
                nodes[ent_2] = ent_id
                if not found_paper and ent_2[1] == 'Paper':
                    paper_end_id = ent_id
                ent_id += 1
            
            source_id = nodes[ent_1]
            target_id = nodes[ent_2]

            # store link number
            link = (source_id, target_id)
            if link not in link_nums:
                link_nums[link] = 1
            else:
                link_nums[link] += 1

            links.append({
                'id': link_id,
                'source': source_id,
                'target': target_id,
                'label': relation_name,
                'linkNum': link_nums[link],
                'counter': 1 if (target_id,source_id) in link_nums else 0,
            })
            link_id += 1
        
        for author in authors:
            author_ent = (author, 'Author',)
            if author_ent not in nodes:
                nodes[author_ent] = ent_id
                author_node_id = ent_id
                ent_id += 1
            else:
                author_node_id = nodes[author_ent]
            links.append({
                'id': link_id,
                'source': author_node_id, 
                'target': paper_end_id,
                'label': 'author_of',
                'linkNum': 1,
                'counter': 0,
            })
            link_id += 1

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

class Key_PaperD3Get(APIView):
    """
    API for retrieving graph containing path between keyword node(s) to paper
    """

    graph_url = f"{GM_URL}/kwGraph"

    def get(self, request, format=None):
        keys = self.request.GET.get('keywords')
        paper_id = self.request.GET.get('paper_id')
        paper_title = Paper.objects.get(pk=paper_id).paper_title
        payload = urllib.parse.urlencode({
            "keys": keys,
            "paper_title": paper_title,
            "limit": self.request.GET.get('limit', 0)
        })

        response = requests.get(self.graph_url,params=payload)
        paths = response.json().get('graph', [])
        
        get_label = lambda x: x[0] if x[0]!='BaseEntity' else x[1] 
        ent_id = 1
        link_id = 1 
        nodes = dict()
        links = list()
        link_nums = dict()
        seen_relation = set()
        for path in paths:
            for relation in path:
                relation_name, ent_1, ent_2 = relation
                ent_1, ent_2 = tuple(ent_1), tuple(ent_2)
                
                if ent_1 not in nodes:
                    nodes[ent_1] = ent_id; ent_id += 1
                if ent_2 not in nodes:
                    nodes[ent_2] = ent_id; ent_id += 1
                
                source_id = nodes[ent_1]
                target_id = nodes[ent_2]

                r = (source_id, target_id, relation_name)
                if r not in seen_relation:
                    link = (source_id, target_id)
                    if link not in link_nums:
                        link_nums[link] = 1
                    else:
                        link_nums[link] += 1
                    links.append({
                        'id': link_id,
                        'source': nodes[ent_1],
                        'target': nodes[ent_2],
                        'label': relation_name,
                        'linkNum': link_nums[link],
                        'counter': 1 if (target_id,source_id) in link_nums else 0,
                    })
                    link_id += 1
                    seen_relation.add(r)

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
    
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        capitalizer = lambda x: string.capwords(x)
        try:
            serializer = PaperSerializer(instance=obj)
            paper = serializer.data
            # paper['conference'] = capitalizer(paper['conference'])
            # paper['authors'] = list(map(capitalizer, paper['authors']))
            # paper['affiliations'] = list(map(capitalizer, paper['affiliations']))
            # paper['affiliations'] = list(dict.fromkeys(paper['affiliations']))
            # if "" in paper['affiliations']:
            #     paper['affiliations'].remove("")
            return Response(paper, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(None, status=status.HTTP_400_BAD_REQUEST)
    
class PaperList(generics.ListAPIView):
    """
    GET Rest API view for requesting papers information.
    """

    # TODO: adding explanation retrieving from graph manager to response 
    explanation_url = f'{GM_URL}/explain'

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
                # paper['conference'] = capitalizer(paper['conference'])
                # paper['authors'] = list(map(capitalizer, paper['authors']))
                # paper['affiliations'] = list(map(capitalizer, paper['affiliations']))
                # paper['affiliations'] = list(dict.fromkeys(paper['affiliations']))
                # if "" in paper['affiliations']:
                #     paper['affiliations'].remove("")
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
                    paper['explanation'] = explanation_json[i][0]
                    paper['explanation_keywords'] = explanation_json[i][1]

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)

class CitePaperPost(APIView):
    """
    Post REST Api for retrieving ref/cite paper list
    """

    def _get_queryset(self, paper_id, query_type, order_by_field, ordering):
        if query_type == 0: #cite_to
            if ordering == 0:
                return (
                    Paper.objects.get(pk=paper_id).cite_to.order_by(f"-{order_by_field}")
                )
            return (
                Paper.objects.get(pk=paper_id).cite_to.order_by(order_by_field)
            )
        elif query_type == 1: #cited_by
            if ordering == 0:
                return (
                    Paper.objects.filter(cite_to=paper_id).order_by(f"-{order_by_field}")
                )
            return (
                Paper.objects.filter(cite_to=paper_id).order_by(order_by_field)
            )

    def get_field_name(self, fid):
        if fid==0:
            return "publish_date"
        elif fid==1:
            return 'citation_count'
        return 'paper_id'

    def post(self, request, *args, **kwargs):
        data = request.data
        paper_id = data['paper_id']
        query_type = data['type'] # 0 for cite_to 1 for cited by
        skip = data['skip']
        order_by_field = self.get_field_name(data['field'])
        ordering = data['ordering'] # 0 for desc 1 for asc


        papers = self._get_queryset(paper_id, query_type, order_by_field, ordering)[skip:skip+10]

        capitalizer = lambda x: string.capwords(x)
        try:
            serializer = PaperListSerializer(instance=papers,many=True)
            response_data = serializer.data
            for paper in response_data:
                paper['conference'] = capitalizer(paper['conference'])
                paper['authors'] = list(map(capitalizer, paper['authors']))
                paper['affiliations'] = list(map(capitalizer, paper['affiliations']))
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response([], status=status.HTTP_400_BAD_REQUEST)
        
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
            - 3 -> BM25
        'sortOrder': <int> sort order
            - 0 -> best first (most popular,citation count, newest)
            - 1 -> opposite to best first
        'filterYear': <str> format start-end ex: '2019-2020'
                        default: not fill it.
    }

    """

    preprocess_url = f"{GM_URL}/preprocess"

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


    def _get_papers(self, keywords, year_range):
        mapping_keyword_id = {}
        papers = []
        for keyword in keywords:
            # regx
            regx = r'\b{}(s|es){{0,1}}\b'.format(keyword)
            if(year_range == 'DEFAULT'):
                temp_papers = Paper.objects.filter(
                    Q(abstract__iregex=regx) | Q(paper_title__iregex=regx)
                )
            else:
                temp_papers = Paper.objects.filter(
                    Q(abstract__iregex=regx) | Q(paper_title__iregex=regx),
                    Q(publish_date__year__gte=int(year_range[0])),
                    Q(publish_date__year__lte=int(year_range[1]))
                )
            mapping_keyword_id[keyword] = [paper.paper_id for paper in temp_papers]
            papers += temp_papers
        return list(set(papers)),mapping_keyword_id

    # def _get_em_scores(self, papers, keywords):
    #     # initial for embbeding vector
    #     W_TITLE = 1
    #     W_ABSTRACT = 1

    #     model = SentenceTransformer('roberta-large-nli-mean-tokens',device='cpu')

    #     title_em = []
    #     abstract_em = []
    #     for paper in papers:
    #         title_em.append(embedding_vector[paper.paper_title]['title_em'])
    #         abstract_em.append(embedding_vector[paper.paper_title]['abstract_em'])

    #     keywords = tuple(keywords)
    #     keywords_em = model.encode(keywords)

    #     scores = {}
    #     for keyword,keyword_em in zip(keywords,keywords_em):
    #         keyword_title_distance = scipy.spatial.distance.cdist([keyword_em], title_em, 'cosine')[0]
    #         keyword_abstract_distance = scipy.spatial.distance.cdist([keyword_em], abstract_em, 'cosine')[0]

    #         for i,paper in enumerate(papers):
    #             if paper.paper_id not in scores:
    #                 scores[paper.paper_id] = (W_TITLE * keyword_title_distance[i]) + (W_ABSTRACT * keyword_abstract_distance[i])

    #     return scores

    def _normalize_score(self,score,old_min,old_max,new_min,new_max):
        normalized_score = (new_max - new_min)*(score - old_min)/(old_max - old_min) + new_min
        return normalized_score


    def get(self, request, format=None):
        """
        Return ranked search result 
        """
        q = request.GET.get('q', '')
        limit = int(request.GET.get('lim',10))
        skip = int(request.GET.get('skip', 0))
        sort_by = int(request.GET.get('sortBy',0))
        sort_order = int(request.GET.get('sortOrder',0))
        filter_year_range = str(request.GET.get('filterYear','DEFAULT')).strip()
        DEBUG = int(request.GET.get('debug',0)) # for debug
        response = requests.post(self.preprocess_url,json={"text": q})
        keywords,cleaned_response = self._get_keys(response.json())
        


        if(filter_year_range == 'DEFAULT'):
            papers,mapping_keyword_id = self._get_papers(keywords,'DEFAULT')
        else: 
            from_year = int(filter_year_range[:4])
            to_year = int(filter_year_range[5:])
            papers,mapping_keyword_id = self._get_papers(keywords,(from_year,to_year))
        
        if DEBUG==1:
            papers_id_title = {}
            for paper in papers:
                if paper.paper_id not in papers_id_title:
                    papers_id_title[paper.paper_id] = paper.paper_title

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
        if(sort_by == 0): #relevance
            for i,paper in enumerate(papers):
                temp_scores[i][2] = paper.popularity
        elif(sort_by == 1): #citation count
            for i,paper in enumerate(papers):
                temp_scores[i][2] = paper.citation_count
        elif(sort_by == 2): #publish date
            for i,paper in enumerate(papers):
                temp_scores[i][2] = paper.publish_date

        # elif(sort_by == 3): # embedding vector
        #     W_EM = 1
        #     W_POP = 1
        #     scores = self._get_em_scores(papers,q) # q is query/ keywords for extracted keyword

        #     l_scores = list(scores.values())
        #     l_popularity = [paper.popularity for paper in papers]
            
        #     for i,paper in enumerate(papers):
        #         normalized_score = self._normalize_score(scores[paper.paper_id],min(l_scores),max(l_scores),0,1)
        #         normalized_pop_score = self._normalize_score(paper.popularity,min(l_popularity),max(l_popularity),0,1)
        #         temp_scores[i][1] = (W_EM * normalized_score) + (W_POP * normalized_pop_score) #ignore n_keywords

        #final_score
        for score in temp_scores:
            papers_score[score[0]] = (score[1],score[2])
        
        #sort keyword score first, then other score
        if(sort_order == 0):
            sorted_papers = [paper_id for paper_id in dict(sorted(papers_score.items(), key=lambda score: (score[1][0],score[1][1]))[::-1]).keys()]
        else:
            sorted_papers = [paper_id for paper_id in dict(sorted(papers_score.items(), key=lambda score: (-score[1][0],score[1][1]))).keys()]

        result_papers = sorted_papers[skip:skip+limit]
        #keyword(s) of each paper
        papers_keyword = {}
        for paper in result_papers:
            if paper not in papers_keyword.keys():
                papers_keyword[paper] = []
            for keyword in mapping_keyword_id.keys():
                if paper in mapping_keyword_id[keyword]:
                    papers_keyword[paper].append(keyword)
        result_keyword = [papers_keyword[paper] for paper in result_papers]
        
        result = {
            'paper_id': result_papers,
            'paper_keywords': result_keyword
        }

        if DEBUG==1:
            result_papers_title = []
            for paper_id in result_papers:
                result_papers_title.append(papers_id_title[paper_id])
            result = {
                'paper_id': result_papers,
                'paper_title': result_papers_title
            }

    

        # print(sorted(papers_score.items(), key=lambda score: (score[1][0],score[1][1]))[::-1])
        return Response(result, status=status.HTTP_200_OK)

class FactGet(APIView):
    """
    API for retrieving fact list
    """

    keys = ['key', 'n_labels', 'type', 'isSubject', 'name', 'm_labels']
    url = f"{GM_URL}/facts"
    relation_format = {
        ('hyponym_of', True): '{} is a subtype of...',
        ('hyponym_of', False): "{}'s subtypes",
        ('refer_to', True): '{} referred to...',
        ('refer_to', False): '{} can be referred by..',
        ('used_for', True): '{} is used for...',
        ('used_for', False): '{} is used by...',
        ('feature_of', True): '{} is a feature of...',
        ('feature_of', False): "{}'s features",
        ('evaluate_for', True): '{} is evaluate for...',
        ('evaluate_for', False): '{} is evaluated by...',
        ('part_of', True): '{} is part of...',
        ('part_of', False): "{}'s parts",
        ('compare', None): '{} is compared to...',
        ('related_to', None): '{} is related to...',
    }

    def rename_relation(self, relation_type, isSubject, n):
        if relation_type=='compare' or relation_type=='related_to':
            return self.relation_format.get((relation_type, None), '{}').format(n)
        return self.relation_format.get((relation_type, isSubject), '{}').format(n)

    def relation_restruct(self, fact):
        get_label = lambda x: x[0] if x[0]!='BaseEntity' else x[1]
        n_name, n_label, relation_type, isSubject, m_name, m_label = [fact.get(k) for k in self.keys]
        n_label = get_label(n_label)
        m_label = get_label(m_label)
        n = n_name
        m = m_name
        relation_name = self.rename_relation(relation_type, isSubject,n)
        return relation_name, m, m_label, n_label 
    
    def restruct_facts(self, fact_list):
        
        relations = dict()

        for fact in fact_list:
            paper_set = set()
            paper_list = []
            
            for paper_id in fact['papers']:
                if paper_id not in paper_set:
                    paper_set.add(paper_id)
                    try: 
                        # paper_title = Paper.objects.get(pk=paper_id).paper_title
                        paper_title = Paper.objects.filter(arxiv_id=paper_id).values_list('paper_title')
                        print(paper_title)
                        paper_list.append({'id':paper_id, 'title':paper_title})
                    except Paper.DoesNotExist:
                        continue
            
            relation_name, m, m_label, n_label = self.relation_restruct(fact)
            relation_name = (relation_name, n_label)
            r_dict = {
                'm': m,
                'm_label': m_label,
                'paper_list': paper_list,
            }

            if relation_name not in relations:
                relations[relation_name] = [r_dict]
            else:
                relations[relation_name].append(r_dict)
            
        ret = []
        for k,v in relations.items():
            d = {
                'relation_name': k[0],
                'n_label': k[1],
                'relations': v
            }
            ret.append(d)
        return ret

    def get(self, request, format=None):
        q = request.GET.get('q')
        # TODO: check q value
        payload = urllib.parse.urlencode({"q": q})
        response = requests.get(self.url,params=payload)
        print(response.status_code)
        facts = response.json().get('facts', [])

        fact_list = self.restruct_facts(facts)
        # for fact in fact_list:
        #     paper_set = set()
        #     for i,paper_id in enumerate(fact['papers']):
        #         if paper_id not in paper_set:
        #             paper_set.add(paper_id)
        #             paper_title = Paper.objects.get(pk=paper_id).paper_title
        #             fact['papers'][i] = {'id':paper_id, 'title':paper_title}

        node_dict = dict()
        links = []
        link_id = 1 
        link_nums = dict()
        ent_id = 1
        get_label = lambda x: x[0] if x[0]!='BaseEntity' else x[1]
        get_source_target = lambda n,m,x: (n,m) if x else (m,n)  
        # n_name = facts[0]['key']
        # n_label = get_label(facts[0]['n_labels'])
        # n = (n_name, n_label,)
        # node_dict[n] = ent_id
        # n_id = 1
        # ent_id += 1
        keys = self.keys
        for fact in facts:
            n_name, n_label, relation_type, isSubject, m_name, m_label = [fact.get(k) for k in keys]
            # reassure that isSubject is a boolean type var 
            if type(isSubject) == string:
                isSubject = True if isSubject=='true' else False
            n_label = get_label(n_label)
            n = (n_name, n_label,)
            m_label = get_label(m_label)
            m = (m_name, m_label,)
            if n not in node_dict:
                node_dict[n] = ent_id
                n_id = ent_id
                ent_id += 1
            if m not in node_dict:
                node_dict[m] = ent_id
                m_id = ent_id
                ent_id += 1
            n_id = node_dict[n]
            m_id = node_dict[m]
            source, target = get_source_target(n_id,m_id,isSubject)

            # store link number
            link = (source, target)
            if link not in link_nums:
                link_nums[link] = 1
            else:
                link_nums[link] += 1
            links.append({
                'id': link_id,
                'source': source,
                'target': target,
                'label': relation_type,
                'linkNum': link_nums[link],
                'counter': 1 if (target,source) in link_nums else 0,
            })
            link_id += 1
        
        node_list = []
        for (ent, eid) in node_dict.items():
            ent_name, ent_label = ent
            node_list.append({
                'id': eid,
                'name': ent_name,
                'labels': ent_label
            })
        data = {'facts': fact_list, 'nodes':node_list, 'links':links}
        return Response(data,status=status.HTTP_200_OK)

class ElasticSearchGet(APIView):

    preprocess_url = f"{GM_URL}/preprocess"

    def __send_response(self, message, status_code, data=None):
        content = {
            "message": message,
            "result": data if data is not None else []
            }
        return Response(content, status=status_code)

    def _normalize_score(self,score,old_min,old_max,new_min,new_max):
        normalized_score = (new_max - new_min)*(score - old_min)/(old_max - old_min) + new_min
        return normalized_score

    def _get_synonym(self,q,ppc):
        synonyms = []
        for key,value in ppc.items():
            if key in q and len(value) > 0:
                synonyms.append(key+" ,"+value[0])
        return synonyms


    def get(self, request):
        query = request.GET.get('q', None)
        k = 100
        limit = int(request.GET.get('lim',10))
        skip = int(request.GET.get('skip', 0))
        sort_by = int(request.GET.get('sortBy',0))
        sort_order = int(request.GET.get('sortOrder',0))
        filter_year_range = str(request.GET.get('filterYear','DEFAULT')).strip()
        DEBUG = int(request.GET.get('debug',0)) # for debug

        one_keyword = False
        if len(query.split()) == 1:
            one_keyword = True


        if is_empty_or_null(query):
            error_message = "queries should not be empty"
            return self.__send_response(error_message, status.HTTP_400_BAD_REQUEST)

        if is_empty_or_null(k):
            error_message = "k should be integer and not empty"
            return self.__send_response(error_message, status.HTTP_400_BAD_REQUEST)

        ppc = requests.post(self.preprocess_url,json={"text": query})
        synonyms = self._get_synonym(query,ppc.json())


        len_phrase = 0
        len_and = 0
        len_or = 0

        try:
            # rebuild_elasticsearch_index(
            if not one_keyword:
                if filter_year_range == 'DEFAULT':
                    search_doc = ElasticSearchPaperPhraseService(PaperDocument, query, k)
                else:
                    from_year = int(filter_year_range[:4])
                    to_year = int(filter_year_range[5:])
                    filter_year_range = (from_year,to_year)
                    search_doc = ElasticSearchPaperPhraseService(PaperDocument, query, k, filter_year_range)

                result_phrase = search_doc.run_query_list()
                len_phrase = len(result_phrase) 

            if len_phrase < k:
                if filter_year_range == 'DEFAULT':
                    search_doc = ElasticSearchPaperAndService(PaperDocument, query, k-len_phrase)
                else:
                    from_year = int(filter_year_range[:4])
                    to_year = int(filter_year_range[5:])
                    filter_year_range = (from_year,to_year)
                    search_doc = ElasticSearchPaperFilterAndService(PaperDocument, query, k-len_phrase, filter_year_range)

                result_and = search_doc.run_query_list()
                len_and = len(result_and)

            if (len_phrase+len_and) < k:
                if filter_year_range == 'DEFAULT':
                    search_doc = ElasticSearchPaperOrService(PaperDocument, query, k-(len_phrase+len_and))
                else:
                    from_year = int(filter_year_range[:4])
                    to_year = int(filter_year_range[5:])
                    filter_year_range = (from_year,to_year)
                    search_doc = ElasticSearchPaperFilterOrService(PaperDocument, query, k-(len_phrase+len_and), filter_year_range)

                result_or = search_doc.run_query_list()
                len_or = len(result_or)
            # delete_elasticsearch_index()
     
        
        except elasticsearch.ConnectionError as connection_error:
            error_message = "Elastic search Connection refused"
            return self.__send_response(error_message, status.HTTP_503_SERVICE_UNAVAILABLE)

        except Exception as exception_msg:
            error_message = str(exception_msg)
            return self.__send_response(error_message, status.HTTP_400_BAD_REQUEST)


        paper_title = {}
        paper_id = []
        papers_phrase = {}
        papers_and = {}
        papers_or = {}


        if len_phrase > 0:
            max_score_phrase = 0
            min_score_phrase = 0
            max_pop_phrase = 0
            min_pop_phrase = 0
            for paper in result_phrase:
                paper_id.append(paper['_id'])
                paper_title[paper['_id']] = paper['_source']['paper_title']

                if sort_by == 0: #relevance
                    if paper['_id'] not in papers_phrase:
                        papers_phrase[paper['_id']] = [0,0]
                    papers_phrase[paper['_id']][0] = paper['_score']
                    publish_date = datetime.datetime.strptime(paper['_source']['publish_date'], '%Y-%m-%d').date()
                    diff_date = datetime.date.today() - publish_date
                    popularity = int(paper['_source']['citation_count']) / diff_date.days
                    papers_phrase[paper['_id']][1] = popularity

                    if float(paper['_score']) > max_score_phrase:
                        max_score_phrase = float(paper['_score'])
                    if float(paper['_score']) < min_score_phrase:
                        min_score_phrase = float(paper['_score'])
                    if popularity > max_pop_phrase:
                        max_pop_phrase = popularity
                    if popularity < min_pop_phrase:
                        min_pop_phrase = popularity
                
                elif sort_by==1: #citation_count
                    papers_phrase[paper['_id']] = paper['_source']['citation_count']
                
                elif sort_by==2: #publish_date
                    papers_phrase[paper['_id']] = datetime.datetime.strptime(paper['_source']['publish_date'], '%Y-%m-%d').date()
        
        if len_phrase < k:
            max_score_and = 0
            min_score_and = 0
            max_pop_and = 0
            min_pop_and = 0
            print('hi')
            for paper in result_and:
                if paper['_id'] not in paper_id:
                    paper_id.append(paper['_id'])
                    paper_title[paper['_id']] = paper['_source']['paper_title']

                    if sort_by == 0: #relevance
                        if paper['_id'] not in papers_and:
                            papers_and[paper['_id']] = [0,0]
                        papers_and[paper['_id']][0] = paper['_score']
                        publish_date = datetime.datetime.strptime(paper['_source']['publish_date'], '%Y-%m-%d').date()
                        diff_date = datetime.date.today() - publish_date
                        popularity = int(paper['_source']['citation_count']) / diff_date.days
                        papers_and[paper['_id']][1] = popularity

                        if float(paper['_score']) > max_score_and:
                            max_score_and = float(paper['_score'])
                        if float(paper['_score']) < min_score_and:
                            min_score_and = float(paper['_score'])
                        if popularity > max_pop_and:
                            max_pop_and = popularity
                        if popularity < min_pop_and:
                            min_pop_and = popularity
                    
                    elif sort_by==1: #citation_count
                        papers_and[paper['_id']] = paper['_source']['citation_count']
                    
                    elif sort_by==2: #publish_date
                        papers_and[paper['_id']] = datetime.datetime.strptime(paper['_source']['publish_date'], '%Y-%m-%d').date()

        if (len_phrase+len_and) < k:
            max_score_or = 0
            min_score_or = 0
            max_pop_or = 0
            min_pop_or =0
            for paper in result_or:
                if paper['_id'] not in paper_id:
                    paper_id.append(paper['_id'])
                    paper_title[paper['_id']] = paper['_source']['paper_title']

                    if sort_by == 0: #relevance
                        if paper['_id'] not in papers_or:
                            papers_or[paper['_id']] = [0,0]
                        papers_or[paper['_id']][0] = paper['_score']
                        publish_date = datetime.datetime.strptime(paper['_source']['publish_date'], '%Y-%m-%d').date()
                        diff_date = datetime.date.today() - publish_date
                        popularity = int(paper['_source']['citation_count']) / diff_date.days
                        papers_or[paper['_id']][1] = popularity

                        if float(paper['_score']) > max_score_or:
                            max_score_or = float(paper['_score'])
                        if float(paper['_score']) < min_score_or:
                            min_score_or = float(paper['_score'])
                        if popularity > max_pop_or:
                            max_pop_or = popularity
                        if popularity < min_pop_or:
                            min_pop_or = popularity
                    
                    elif sort_by==1: #citation_count
                        papers_or[paper['_id']] = paper['_source']['citation_count']
                    
                    elif sort_by==2: #publish_date
                        papers_or[paper['_id']] = datetime.datetime.strptime(paper['_source']['publish_date'], '%Y-%m-%d').date()
    


        if sort_by==0:
            W_ELASTIC_SCORE = 0.5
            W_POPULARITY = 0.5

            if len_phrase > 0:
                for key in papers_phrase.keys():
                    papers_phrase[key][0] = self._normalize_score(papers_phrase[key][0],min_score_phrase,max_score_phrase,0,1)
                    papers_phrase[key][1] = self._normalize_score(papers_phrase[key][1],min_pop_phrase,max_pop_phrase,0,1)
                    papers_phrase[key] = (W_ELASTIC_SCORE * papers_phrase[key][0]) + (W_POPULARITY * papers_phrase[key][1])
            
            if len_phrase < k:
                for key in papers_and.keys():
                    papers_and[key][0] = self._normalize_score(papers_and[key][0],min_score_and,max_score_and,0,1)
                    papers_and[key][1] = self._normalize_score(papers_and[key][1],min_pop_and,max_pop_and,0,1)
                    papers_and[key] = (W_ELASTIC_SCORE * papers_and[key][0]) + (W_POPULARITY * papers_and[key][1])
            
            if (len_phrase+len_and) < k:
                for key in papers_or.keys():
                    papers_or[key][0] = self._normalize_score(papers_or[key][0],min_score_or,max_score_or,0,1)
                    papers_or[key][1] = self._normalize_score(papers_or[key][1],min_pop_or,max_pop_or,0,1)
                    papers_or[key] = (W_ELASTIC_SCORE * papers_or[key][0]) + (W_POPULARITY * papers_or[key][1])


        sorted_papers = []
        if sort_order==0:
            if len_phrase > 0:
                sorted_papers += [paper_id for paper_id in dict(sorted(papers_phrase.items(), key=lambda x: x[1])[::-1]).keys()]
            if len_phrase < k:
                sorted_papers += [paper_id for paper_id in dict(sorted(papers_and.items(), key=lambda x: x[1])[::-1]).keys()][:k-len_phrase]
            if (len_phrase+len_and) < k:
                sorted_papers += [paper_id for paper_id in dict(sorted(papers_or.items(), key=lambda x: x[1])[::-1]).keys()][:k-(len_phrase+len_and)]
        elif sort_order==1:
            if len_phrase > 0:
                sorted_papers = [paper_id for paper_id in dict(sorted(papers_phrase.items(), key=lambda x: x[1])).keys()]
            if len_phrase < k:
                sorted_papers += [paper_id for paper_id in dict(sorted(papers_and.items(), key=lambda x: x[1])).keys()][:k-len_phrase]
            if (len_phrase+len_and) < k:
                sorted_papers += [paper_id for paper_id in dict(sorted(papers_or.items(), key=lambda x: x[1])).keys()][:k-(len_phrase+len_and)]
            

        final_result = sorted_papers[skip:skip+limit]
        
        if DEBUG==1:
            print('phrase:',len_phrase,'/','and:',len_and,'/','or:',len_or)
            final_result = [paper_title[paper_id] for paper_id in final_result]

        response = final_result
        # print(sorted_papers)

        return self.__send_response('success', status.HTTP_200_OK, response)