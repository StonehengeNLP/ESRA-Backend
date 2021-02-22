from elasticsearch_dsl import Q
import datetime
from .documents import custom_analyzer

class ElasticSearchPaperAndService:

    def __init__(self, document_class_name, query, size):
        self.query = query
        self.size = size
        self.search_instance = document_class_name.search()

    """ 
    filter papers using query from given query list
    """
    def run_query_list(self):

        filter_words = ['using','with','in','on','by']
        self.query = " ".join([word for word in self.query.split() if word.lower() not in filter_words])

        q = Q({"multi_match": { "query": self.query, "fields": ["paper_title", "abstract"], "operator": "and", "type": "bool_prefix", "analyzer": custom_analyzer}})
        # q = Q('bool',must=[Q('match', paper_title=self.query), Q('match', abstract=self.query),])

        search_with_query = self.search_instance.query(q).sort('_score')[0:self.size]
        # search_with_query = self.search_instance.query(q).sort('_score')

        response = search_with_query.execute()
        result = response.to_dict()['hits']['hits']

        return result


class ElasticSearchPaperFilterAndService:

    def __init__(self, document_class_name, query, size,  filter_year_range):
        self.filter_year_range = filter_year_range
        self.query = query
        self.size = size
        self.search_instance = document_class_name.search()

    """ 
    filter papers using query from given query list
    """
    def run_query_list(self):
        filter_words = ['using','with','in','on','by']
        self.query = " ".join([word for word in self.query.split() if word.lower() not in filter_words])

        from_year = datetime.datetime.strptime(str(self.filter_year_range[0])+'-01-01','%Y-%m-%d').date()
        to_year = datetime.datetime.strptime(str(self.filter_year_range[1])+'-01-01','%Y-%m-%d').date()

        q = Q({"multi_match": { "query": self.query, "fields": ["paper_title", "abstract"], "operator": "and", "type": "bool_prefix", "analyzer": custom_analyzer}})
        self.search_instance = self.search_instance.query(q)
        self.search_instance = self.search_instance.filter('range', **{'publish_date': { 'gte': from_year,'lt': to_year}})
        
        # search_with_query = self.search_instance.sort('_score')
        search_with_query = self.search_instance.query(q).sort('_score')[0:self.size]


        response = search_with_query.execute()
        result = response.to_dict()['hits']['hits']

        return result

class ElasticSearchPaperOrService:

    def __init__(self, document_class_name, query, size):
        self.query = query
        self.size = size
        self.search_instance = document_class_name.search()

    """ 
    filter papers using query from given query list
    """
    def run_query_list(self):
        filter_words = ['using','with','in','on','by']
        self.query = " ".join([word for word in self.query.split() if word.lower() not in filter_words])

        q = Q({"multi_match": { "query": self.query, "fields": ["paper_title", "abstract"], "operator": "or", "type": "bool_prefix", "analyzer": custom_analyzer}})
        # q = Q('bool',must=[Q('match', paper_title=self.query), Q('match', abstract=self.query),])

        # search_with_query = self.search_instance.query(q).sort('_score')
        search_with_query = self.search_instance.query(q).sort('_score')[0:self.size]


        response = search_with_query.execute()
        result = response.to_dict()['hits']['hits']

        return result


class ElasticSearchPaperFilterOrService:

    def __init__(self, document_class_name, query, size, filter_year_range):
        self.filter_year_range = filter_year_range
        self.query = query
        self.size = size
        self.search_instance = document_class_name.search()

    """ 
    filter papers using query from given query list
    """
    def run_query_list(self):
        filter_words = ['using','with','in','on','by']
        self.query = " ".join([word for word in self.query.split() if word.lower() not in filter_words])

        from_year = datetime.datetime.strptime(str(self.filter_year_range[0])+'-01-01','%Y-%m-%d').date()
        to_year = datetime.datetime.strptime(str(self.filter_year_range[1])+'-01-01','%Y-%m-%d').date()

        q = Q({"multi_match": { "query": self.query, "fields": ["paper_title", "abstract"], "operator": "or", "type": "bool_prefix", "analyzer": custom_analyzer}})
        self.search_instance = self.search_instance.query(q)
        self.search_instance = self.search_instance.filter('range', **{'publish_date': { 'gte': from_year,'lt': to_year}})
        
        # search_with_query = self.search_instance.sort('_score')
        search_with_query = self.search_instance.query(q).sort('_score')[0:self.size]


        response = search_with_query.execute()
        result = response.to_dict()['hits']['hits']

        return result
