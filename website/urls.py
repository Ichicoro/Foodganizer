from django.urls import path, include
from django.contrib.auth import views as auth_views

from . import views
from . import api_endpoints

urlpatterns = [
    path('', views.index, name='index'),
    path('signup', views.signup, name='signup'),
    path('login', auth_views.LoginView.as_view(), name='login'),
    path('profile', views.profile, name='profile'),
    path('profile/<slug:username>', views.view_profile, name='otherprofile'),
    path('quaggatest', views.quaggatest, name='quaggatest'),
    path('logout', auth_views.LogoutView.as_view(
        extra_context={
            'next': '/',
        },
    ), name='logout'),
    path('kitchens', views.kitchens, name='kitchens'),
    path('kitchens/new', views.new_kitchen, name='new_kitchen'),
    path('kitchens/share/<uuid:share_uuid>', views.shared_kitchen, name='share_kitchen_link'),
    path('kitchens/<int:id>', views.kitchen, name='kitchen'),
    path('kitchens/<int:id>/invite', views.invite_users, name='kitchen_invite_users'),
    path('memberships/<int:id>/delete', views.delete_membership, name='delete_membership'),
    path('memberships/<int:id>/promote', views.promote_membership, name='promote_membership'),
    path('kitchens/<int:id>/share', views.set_kitchen_sharing, name='set_kitchen_sharing'),
    path('kitchens/<int:id>/join', views.join_kitchen, name='join_kitchen'),

    path('kitchens/<int:id>/stored/add', views.add_storeditem_kitchen, name='add_storeditem_kitchen'),
    path('kitchens/<int:id>/stored/delete', views.delete_storeditem_kitchen, name='delete_storeditem_kitchen'),
    path('kitchens/<int:id>/stored/update/<int:item_id>', views.update_storeditem_kitchen, name='update_storeditem_kitchen'),
    path('kitchens/<int:id>/stored/move/<int:item_id>', views.move_storeditem_kitchen, name='move_storeditem_kitchen'),

    path('kitchens/<int:id>/cart/add', views.add_cartitem_kitchen, name='add_cartitem_kitchen'),
    path('kitchens/<int:id>/cart/update/<int:item_id>', views.update_cartitem_kitchen, name='update_cartitem_kitchen'),
    path('kitchens/<int:id>/cart/delete/<int:item_id>', views.delete_cartitem_kitchen, name='delete_cartitem_kitchen'),
    path('kitchens/<int:id>/cart/move/<int:item_id>', views.move_cartitem_kitchen, name='move_cartitem_kitchen'),

    path('kitchens/<int:id>/new', views.new_kitchen_item, name='new_kitchen_item'),
    path('kitchens/<int:id>/custom/delete/<int:item_id>', views.delete_customitem_kitchen, name='delete_customitem_kitchen'),

    path('kitchens/<int:id>/postit/new', views.create_postit, name='create_postit'),
    path('kitchens/<int:id>/postit/edit/<int:postit_id>', views.edit_postit, name='edit_postit'),
    path('kitchens/<int:id>/postit/delete/<int:postit_id>', views.delete_postit, name='delete_postit'),

    path('api/products/search', api_endpoints.search_products, name='search_products_api'),
    path('api/product/search', api_endpoints.get_product_by_code, name='check_product_exists_api')

]