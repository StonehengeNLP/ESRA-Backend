from django.urls import path,include
from .views import (PaperGet, PaperList, PaperPost, 
                    AuthorPost, AffiliationPost, PaperAuthorAffilationPost,
                    SearchGet, AutoComplete, GraphGet, PaperD3Get)

urlpatterns = [

    path('api/',
        include('rest_framework.urls',namespace='rest_framework')
    ),
    path(
        'complete',
        AutoComplete.as_view(),
        name='auto_complete'
    ),
    path(
        'graph',
        GraphGet.as_view(),
        name='get_graph'
    ),
    path(
        'graph_d3',
        PaperD3Get.as_view(),
        name='d3'
    ),
    path(
        'paper/get_paper',
        PaperGet.as_view(),
        name='get_paper'
    ),
    path(
        'paper/paper_list',
        PaperList.as_view(),
        name='paper_list'
    ),
    path(
        'paper/create',
        PaperPost.as_view(),
        name='paper_create'
    ),
    path(
        'author/create',
        AuthorPost.as_view(),
        name='author_create'
    ),
    path(
        'affiliation/create',
        AffiliationPost.as_view(),
        name='affiliations_create'
    ),
    path(
        'paper_relations/create',
        PaperAuthorAffilationPost.as_view(),
        name='paper_relations_create'
    ),
    path(
        'search',
        SearchGet.as_view(),
        name='search'
    ),
    
]