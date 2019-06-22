"""example URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from .views import *

urlpatterns = [
    path('api/article/', ArticleView.as_view(), name='api_articles'),
    path('api/article/<int:id>', ArticleView.as_view(), name='api_article'),
    path('api/tag/', TagView.as_view(), name='api_tags'),
    path('api/tag/<int:id>', TagView.as_view(), name='api_tag'),
    path('api/corpus/', CorpusView.as_view(), name='api_corpuss'),
    path('api/corpus/<int:id>', CorpusView.as_view(), name='api_corpus'),
    path('api/image/', ImageView.as_view(), name='api_references'),
    path('api/image/<int:id>', ImageView.as_view(), name='api_reference'),
]
