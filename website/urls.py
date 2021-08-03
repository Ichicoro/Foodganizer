from django.urls import path, include
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    # ex: /
    path('', views.index, name='index'),
    path('login', auth_views.LoginView.as_view()),
    # # ex: /polls/5/
    # path('<int:question_id>/', views., name='detail'),
    # # ex: /polls/5/results/
    # path('<int:question_id>/results/', views.results, name='results'),
    # # ex: /polls/5/vote/
    # path('<int:question_id>/vote/', views.vote, name='vote'),
]