from elasticsearch_dsl import analyzer
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl.connections import connections
from .models import Paper
from elasticsearch_dsl import analyzer, token_filter, tokenizer
import os
from django.conf import settings


connections.create_connection(hosts=['localhost'])


synonym_tokenfilter = token_filter(
    'synonym_tokenfilter',
    'synonym',
    synonyms_path="analysis/synonyms.txt",
)

custom_analyzer = analyzer(
    "custom_analyzer",
    type="custom",
    tokenizer="standard",
    filter=[
        'lowercase',
        synonym_tokenfilter,
    ]
)

try:
    custom_analyzer.simulate('blah blah')
except Exception as e:
    ex = e
    print(ex)



@registry.register_document
class PaperDocument(Document):

    paper_title = fields.TextField(
        analyzer=custom_analyzer
    )
    abstract = fields.TextField(
        analyzer=custom_analyzer
    )


    class Index:
        name = 'papers' # name of elastic index
        # See Elasticsearch Indices API reference for available settings
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = Paper
        # fields = ['paper_id','citation_count','publish_date','paper_title','abstract']
        fields = ['paper_id','citation_count','publish_date']





    