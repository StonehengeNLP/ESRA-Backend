from django.urls import path,include
from .views import *

urlpatterns = [

    path('api/',
        include('rest_framework.urls',namespace='rest_framework')
    ),
    path(
        'paper/',
        GetPaper.as_view(),
        name='get_paper'
    ),
]