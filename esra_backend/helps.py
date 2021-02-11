from elasticsearch_dsl import Q
import datetime

class ElasticSearchPaperService:

    def __init__(self, document_class_name, query, size):
        self.query = query
        self.size = size
        self.search_instance = document_class_name.search()

    """ 
    filter papers using query from given query list
    """
    def run_query_list(self):
        q = Q('bool',must=[Q('match', paper_title=self.query), Q('match', abstract=self.query),])

        search_with_query = self.search_instance.query(q).sort('_score')[0:self.size]

        response = search_with_query.execute()
        result = response.to_dict()['hits']['hits']

        return result


class ElasticSearchPaperFilterService:

    def __init__(self, document_class_name, query, size, filter_year_range):
        self.filter_year_range = filter_year_range
        self.query = query
        self.size = size
        self.search_instance = document_class_name.search()

    """ 
    filter papers using query from given query list
    """
    def run_query_list(self):
        from_year = datetime.datetime.strptime(str(self.filter_year_range[0])+'-01-01','%Y-%m-%d').date()
        to_year = datetime.datetime.strptime(str(self.filter_year_range[1])+'-01-01','%Y-%m-%d').date()

        self.search_instance = self.search_instance.query('match', paper_title=self.query)
        self.search_instance = self.search_instance.query('match', abstract=self.query)
        self.search_instance = self.search_instance.filter('range', **{'publish_date': { 'gte': from_year,'lt': to_year}})
        
        search_with_query = self.search_instance.sort('_score')[0:self.size]

        response = search_with_query.execute()
        result = response.to_dict()['hits']['hits']

        return result
