# from django.shortcuts import render
# from django.http import HttpResponse
from numpy.lib.utils import source
import requests, string
import urllib.parse
from rest_framework import permissions, serializers, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response 
from .models import *
from django.db.models import Q
from rank_bm25 import BM25Okapi
from .serializer import (PaperSerializer, AuthorSerializer, PaperListSerializer,
                         AffiliationSerializer, PaperAuthorAffiliationSerializer)
from time import sleep
import os
from django.conf import settings
import pickle
from sentence_transformers import SentenceTransformer
import scipy
# from .data import embedding_vector

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

    graph_url = "http://35.247.162.211/kwGraph"

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
                paper['affiliations'] = list(dict.fromkeys(paper['affiliations']))
                if "" in paper['affiliations']:
                    paper['affiliations'].remove("")
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
                Paper.objects.filter(cite_to=paper_id).order_by(f"-{order_by_field}")
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

    """
    def _get_em_scores(self, papers, keywords):
        # initial for embbeding vector
        W_TITLE = 1
        W_ABSTRACT = 1

        # with open(os.path.join(settings.BASE_DIR, 'embedding.pickle'),'rb') as f:
        #     embedding_vector = pickle.load(f)
        model = SentenceTransformer('roberta-large-nli-mean-tokens',device='cpu')

        title_em = []
        abstract_em = []
        for paper in papers:
            title_em.append(embedding_vector[paper.paper_title]['title_em'])
            abstract_em.append(embedding_vector[paper.paper_title]['abstract_em'])

        keywords = tuple(keywords)
        keywords_em = model.encode(keywords)

        scores = {}
        for keyword,keyword_em in zip(keywords,keywords_em):
            keyword_title_distance = scipy.spatial.distance.cdist([keyword_em], title_em, 'cosine')[0]
            keyword_abstract_distance = scipy.spatial.distance.cdist([keyword_em], abstract_em, 'cosine')[0]

            for i,paper in enumerate(papers):
                if paper.paper_id not in scores:
                    scores[paper.paper_id] = (W_TITLE * keyword_title_distance[i]) + (W_ABSTRACT * keyword_abstract_distance[i])

        return scores

    def _normalize_score(self,score,old_min,old_max,new_min,new_max):
        normalized_score = (new_max - new_min)*(score - old_min)/(old_max - old_min) + new_min
        return normalized_score
    """


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

        """
        elif(sort_by == 3): # embedding vector
            W_EM = 1
            W_POP = 1
            scores = self._get_em_scores(papers,keywords)

            l_scores = list(scores.values())
            l_popularity = [paper.popularity for paper in papers]
            
            for i,paper in enumerate(papers):
                normalized_score = self._normalize_score(scores[paper.paper_id],min(l_scores),max(l_scores),0,1)
                normalized_pop_score = self._normalize_score(paper.popularity,min(l_popularity),max(l_popularity),0,1)
                temp_scores[i][1] = (W_EM * normalized_score) + (W_POP * normalized_pop_score) #ignore n_keywords
        """

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
    url = "http://35.247.162.211/facts"
    relation_format = {
        ('hyponym_of', True): '{} is a hyponym of',
        ('hyponym_of', False): 'Hyponyms of {}',
        ('refer_to', True): '{} refer to',
        ('refer_to', False): '{} can be refer by',
        ('used_for', True): '{} is used for',
        ('used_for', False): '{} is used by',
        ('feature_of', True): '{} is a feature of',
        ('feature_of', False): "{}'s features",
        ('evaluate_for', True): '{} is evaluate for',
        ('evaluate_for', False): '{} is evaluated by',
        ('part_of', True): '{} is part of',
        ('part_of', False): "{}'s parts",
        ('compare', None): '{} is compared to',
        ('related_to', None): '{} is related to',
    }

    def rename_relation(self, relation_type, isSubject, n):
        if relation_type=='compare' or relation_type=='related_to':
            return self.relation_format.get((relation_type, None), '{}').format(n)
        return self.relation_format.get((relation_type, isSubject), '{}').format(n)

    def relation_restruct(self, fact):
        n_name, n_label, relation_type, isSubject, m_name, m_label = [fact.get(k) for k in self.keys]
        
        if isSubject:
            n = f"{n_name}({n_label})"
            m = f"{m_name}({m_label})"
        else:
            n = f"{m_name}({m_label})"
            m = f"{n_name}({n_label})"

        relation_name = self.rename_relation(relation_type, isSubject,n)
        return relation_name, m 
    
    def restruct_facts(self, fact_list):
        
        relations = dict()

        for fact in fact_list:
            paper_set = set()
            paper_list = []
            
            for paper_id in fact['papers']:
                if paper_id not in paper_set:
                    paper_set.add(paper_id)
                    paper_title = Paper.objects.get(pk=paper_id).paper_title
                    paper_list.append({'id':paper_id, 'title':paper_title})
            
            relation_name, m = self.relation_restruct(fact)

            r_dict = {
                'm': m,
                'paper_list': paper_list,
            }

            if relation_name not in relations:
                relations[relation_name] = [r_dict]
            else:
                relations[relation_name].append(r_dict)
            
        ret = []
        for k,v in relations.items():
            d = {
                'relation_name': k,
                'relations': v
            }
            ret.append(d)
        return ret

    def get(self, request, format=None):
        q = request.GET.get('q')
        # TODO: check q value
        payload = urllib.parse.urlencode({"q": q})
        response = requests.get(self.url,params=payload)
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
            links.append({
                'source': source,
                'target': target,
                'label': relation_type
            })
        
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