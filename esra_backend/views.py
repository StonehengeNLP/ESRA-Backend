import os
import scipy
import pickle
from sentence_transformers import SentenceTransformer

# from django.shortcuts import render
# from django.http import HttpResponse
from rest_framework import permissions, status, generics
# from rest_framework.views import APIView
# from rest_framework.response import Response 
from .models import *
from .serializer import PaperSerializer


# NOTE: Prepare model and data
view_dir = os.path.dirname(__file__)
vocab_path = os.path.join(view_dir, 'data/vocab.txt')
vocab_embeddings_path = os.path.join(view_dir, 'data/vocab_embeddings.pickle')

model_roberta = SentenceTransformer('roberta-large-nli-mean-tokens')
with open(vocab_path, encoding='utf-8') as f:
    vocab = [i.strip() for i in f.readlines()]

with open(vocab_embeddings_path, 'rb') as f:
    vocab_embeddings = pickle.load(f)


def _get_word(query, number_top_matches=10):
    """
    Semantic search function
    
    Input:
        query(str): keyword to be searched
    Output:
        dict of keywords and their list of related keywords
    """
    if isinstance(query, str):
        queries = [query]
    elif isinstance(query, list):
        queries = query
        
    query_embeddings = model_roberta.encode(queries)

    out = {}
    
    for query, query_embedding in zip(queries, query_embeddings):
        distances = scipy.spatial.distance.cdist([query_embedding], vocab_embeddings, "cosine")[0]

        results = zip(range(len(distances)), distances)
        results = sorted(results, key=lambda x: x[1])

        out[query] = [(1-distance, vocab[idx]) for idx, distance in results[:number_top_matches]]
    
    return out
    
class PaperGet(generics.ListAPIView):
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
        This will requires JSON body contains list of 'paper_ids' 
        
        :return: [ paper_object_1, ... , paper_object_n ]
        """
        paper_ids = self.request.data.get('paper_ids', None)
        keywords = self.request.data.get('keywords', None)
        
        if paper_ids:
            return self._get_paper_by_ids(paper_ids)
        
        if keywords:
            # TODO: find papers using given keywords
            out = _get_word(keywords)
            print(out)
            paper_ids = [1]
            return self._get_paper_by_ids(paper_ids)