from django.urls import path,include
from .views import PaperGet, GetPapers

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
        'paper/get_papers',
        GetPapers.as_view(),
        name='get_papers'
    ),
]