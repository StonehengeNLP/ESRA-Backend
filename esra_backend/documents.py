from elasticsearch_dsl import analyzer
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl.connections import connections
from .models import Paper


connections.create_connection(hosts=['localhost'])

@registry.register_document
class PaperDocument(Document):

    class Index:
        name = 'papers' # name of elastic index
        # See Elasticsearch Indices API reference for available settings
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = Paper
        fields = ['paper_id','paper_title','citation_count','publish_date','abstract']





    