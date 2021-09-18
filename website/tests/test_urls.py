import uuid
from website.api_endpoints import *
from website.views import * 

from django.test.testcases import TestCase
from django.urls import reverse, resolve


class TestUrls(TestCase):
    def test_index_is_resolved(self):
        url = reverse("index")
        self.assertEqual(resolve(url).func, index)
    
    def test_signup_is_resolved(self):
        url = reverse("signup")
        self.assertEqual(resolve(url).func, signup)
    
    def test_profile_is_resolved(self):
        url = reverse("profile")
        self.assertEqual(resolve(url).func, profile)
    
    def test_otherprofile_is_resolved(self):
        url = reverse("otherprofile", args=["test-user"])
        self.assertEqual(resolve(url).func, view_profile)
    
    def test_quaggatest_is_resolved(self):
        url = reverse("quaggatest")
        self.assertEqual(resolve(url).func, quaggatest)
    
    def test_kitchens_is_resolved(self):
        url = reverse("kitchens")
        self.assertEqual(resolve(url).func, kitchens)
    
    def test_new_kitchen_is_resolved(self):
        url = reverse("new_kitchen")
        self.assertEqual(resolve(url).func, new_kitchen)
    
    def test_share_kitchen_link_is_resolved(self):
        url = reverse("share_kitchen_link", args=[uuid.uuid4()])
        self.assertEqual(resolve(url).func, shared_kitchen)
    
    def test_kitchen_is_resolved(self):
        url = reverse("kitchen", args=[123])
        self.assertEqual(resolve(url).func, kitchen)
    
    def test_kitchen_invite_users_is_resolved(self):
        url = reverse("kitchen_invite_users", args=[123])
        self.assertEqual(resolve(url).func, invite_users)
    
    def test_delete_membership_is_resolved(self):
        url = reverse("delete_membership", args=[123])
        self.assertEqual(resolve(url).func, delete_membership)
    
    def test_set_kitchen_sharing_is_resolved(self):
        url = reverse("set_kitchen_sharing", args=[123])
        self.assertEqual(resolve(url).func, set_kitchen_sharing)
    
    def test_join_kitchen_is_resolved(self):
        url = reverse("join_kitchen", args=[123])
        self.assertEqual(resolve(url).func, join_kitchen)
    
    def test_add_storeditem_kitchen_is_resolved(self):
        url = reverse("add_storeditem_kitchen", args=[123])
        self.assertEqual(resolve(url).func, add_storeditem_kitchen)
    
    def test_delete_storeditem_kitchen_is_resolved(self):
        url = reverse("delete_storeditem_kitchen", args=[123])
        self.assertEqual(resolve(url).func, delete_storeditem_kitchen)
    
    def test_update_storeditem_kitchen_is_resolved(self):
        url = reverse("update_storeditem_kitchen", args=[123, 456])
        self.assertEqual(resolve(url).func, update_storeditem_kitchen)
    
    def test_add_cartitem_kitchen_is_resolved(self):
        url = reverse("add_cartitem_kitchen", args=[123])
        self.assertEqual(resolve(url).func, add_cartitem_kitchen)
    
    def test_update_cartitem_kitchen_is_resolved(self):
        url = reverse("update_cartitem_kitchen", args=[123, 456])
        self.assertEqual(resolve(url).func, update_cartitem_kitchen)
    
    def test_delete_cartitem_kitchen_is_resolved(self):
        url = reverse("delete_cartitem_kitchen", args=[123, 456])
        self.assertEqual(resolve(url).func, delete_cartitem_kitchen)
    
    def test_new_kitchen_item_is_resolved(self):
        url = reverse("new_kitchen_item", args=[123])
        self.assertEqual(resolve(url).func, new_kitchen_item)
    
    def test_delete_customitem_kitchen_is_resolved(self):
        url = reverse("delete_customitem_kitchen", args=[123, 456])
        self.assertEqual(resolve(url).func, delete_customitem_kitchen)
    
    def test_create_postit_is_resolved(self):
        url = reverse("create_postit", args=[123])
        self.assertEqual(resolve(url).func, create_postit)
    
    def test_edit_postit_is_resolved(self):
        url = reverse("edit_postit", args=[123, 456])
        self.assertEqual(resolve(url).func, edit_postit)
    
    def test_delete_postit_is_resolved(self):
        url = reverse("delete_postit", args=[123, 456])
        self.assertEqual(resolve(url).func, delete_postit)
    
    def test_search_products_api_is_resolved(self):
        url = reverse("search_products_api")
        self.assertEqual(resolve(url).func, search_products)
    
    def test_check_product_exists_api_is_resolved(self):
        url = reverse("check_product_exists_api")
        self.assertEqual(resolve(url).func, get_product_by_code)
    