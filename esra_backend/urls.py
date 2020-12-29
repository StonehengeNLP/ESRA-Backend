from django.urls import path,include
from .views import PaperGet, PaperList, PaperPost

urlpatterns = [

    path('api/',
        include('rest_framework.urls',namespace='rest_framework')
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
    
]