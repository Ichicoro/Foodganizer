from django.urls import path, include
from django.contrib.auth import views as auth_views

from . import views
from . import api_endpoints

urlpatterns = [
    path('', views.index, name='index'),
    path('signup', views.signup, name='signup'),
    path('login', auth_views.LoginView.as_view(), name='login'),
    path('profile', views.profile, name='profile'),
    path('profile/<slug:username>', views.profile, name='otherprofile'),  # TODO: create separate view, this is currently useless
    path('quaggatest', views.quaggatest, name='quaggatest'),
    path('logout', auth_views.LogoutView.as_view(
        extra_context={
            'next': '/',
        },
    ), name='logout'),
    path('kitchens', views.kitchens, name='kitchens'),
    path('kitchens/new', views.new_kitchen, name='new_kitchen'),
    path('kitchens/<int:id>', views.kitchen, name='kitchen'),
    path('kitchens/<int:id>/add', views.add_item_kitchen, name='add_item_kitchen'),
    path('kitchens/<int:id>/delete', views.delete_item_kitchen, name='delete_item_kitchen'),
    path('kitchens/<int:id>/update/<int:item_id>', views.update_item_kitchen, name='update_item_kitchen'),
    path('kitchens/<int:id>/new', views.new_kitchen_item, name='new_kitchen_item'),

    path('products/search', api_endpoints.search_products, name='search_products_api')
    # # ex: /polls/5/
    # path('<int:question_id>/', views., name='detail'),
    # # ex: /polls/5/results/
    # path('<int:question_id>/results/', views.results, name='results'),
    # # ex: /polls/5/vote/
    # path('<int:question_id>/vote/', views.vote, name='vote'),
]