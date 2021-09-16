import uuid

from django.contrib import auth
from django.contrib.auth.models import AnonymousUser
from website.views import kitchen, shared_kitchen

from django.db.models.fields import EmailField
from django.test.testcases import TestCase

from website.models import Kitchen, Membership, MembershipStatus, User
from django.test import SimpleTestCase
from django.urls import reverse, resolve



class TestUrls(TestCase):
    def setUp(self):
        self.u:User = User.objects.create(username=f"test-user-1-{uuid.uuid4()}", email="testuser@testdomain.test")
        self.u2:User = User.objects.create(username=f"test-user-2-{uuid.uuid4()}", email="testuser2@testdomain.test")
        self.k:Kitchen = Kitchen.objects.create(name="test-kitchen", public_access_uuid=uuid.uuid4())
        self.m:Membership = Membership.objects.create(user=self.u, kitchen=self.k, status=MembershipStatus.ACTIVE_MEMBERSHIP, is_admin=True)

    def test_index(self):
        res = self.client.get(reverse('index'))
        self.assertEqual(res.status_code, 200)

    def test_signup(self):
        res = self.client.get(reverse('signup'))
        self.assertEqual(res.status_code, 200)

    def test_login(self):
        res = self.client.get(reverse('login'))
        self.assertEqual(res.status_code, 200)
        
    def test_profile(self):
        not_logged_in = self.client.get(reverse('profile'))
        self.client.force_login(user=self.u)
        logged_in = self.client.get(reverse('profile'))
        self.assertEqual(not_logged_in.status_code, 302)
        self.assertEqual(logged_in.status_code, 200)

    def test_otherprofile(self):
        good_res = self.client.get(reverse('otherprofile', args=[self.u.username]))
        bad_res = self.client.get(reverse('otherprofile', args=[self.u.username+"_wrong"]), follow=True)
        self.assertEqual(good_res.status_code, 200)
        self.assertEqual(bad_res.status_code, 404)

    def test_logout(self):
        self.client.force_login(user=self.u)
        self.assertFalse(isinstance(auth.get_user(self.client), AnonymousUser))
        self.client.get(reverse('logout'))
        self.assertTrue(isinstance(auth.get_user(self.client), AnonymousUser))

    def test_kitchens(self):
        anon_res = self.client.get(reverse('kitchens'))
        self.client.force_login(user=self.u)
        auth_res = self.client.get(reverse('kitchens'))
        self.assertEqual(anon_res.status_code, 302)
        self.assertEqual(auth_res.status_code, 200)

    def test_new_kitchen(self):
        self.client.force_login(user=self.u)
        get_res = self.client.get(reverse('new_kitchen'))
        bad_post_res = self.client.post(reverse('new_kitchen'), {
            "invalid-data": "value"
        })
        name = f"{self.u2.username}-test-kitchen"
        good_post_res = self.client.post(reverse('new_kitchen'), {
            "name": name,
            "invite_other_users": self.u2.username
        }, follow=True)
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(bad_post_res.status_code, 400)
        self.assertEqual(good_post_res.status_code, 200)

    def test_share_kitchen_link(self):
        res = self.client.get(reverse('share_kitchen_link', args=[self.k.public_access_uuid]), follow=True)
        self.assertEqual(res.status_code, 200)

    def test_kitchen(self):
        res = self.client.get(reverse('kitchen', args=[self.k.id]), follow=True)
        self.assertEqual(res.status_code, 200)

    def test_kitchen_invite_users(self):
        res = self.client.get(reverse('kitchen_invite_users', args=[self.k.id]), follow=True)
        self.assertEqual(res.status_code, 200)

    # def test_delete_membership(self):
    #     res = self.client.get(reverse('delete_membership'), follow=True)
    #     self.assertEqual(res.status_code, 200)

    # def test_set_kitchen_sharing(self):
    #     res = self.client.get(reverse('set_kitchen_sharing'), follow=True)
    #     self.assertEqual(res.status_code, 200)

    # def test_join_kitchen(self):
    #     res = self.client.get(reverse('join_kitchen'), follow=True)
    #     self.assertEqual(res.status_code, 200)

    # def test_add_storeditem_kitchen(self):
    #     res = self.client.get(reverse('add_storeditem_kitchen'), follow=True)
    #     self.assertEqual(res.status_code, 200)

    # def test_add_cartitem_kitchen(self):
    #     res = self.client.get(reverse('add_cartitem_kitchen'), follow=True)
    #     self.assertEqual(res.status_code, 200)

    # def test_delete_item_kitchen(self):
    #     res = self.client.get(reverse('delete_item_kitchen'), follow=True)
    #     self.assertEqual(res.status_code, 200)

    # def test_delete_item_kitchen(self):
    #     res = self.client.get(reverse('delete_item_kitchen'), follow=True)
    #     self.assertEqual(res.status_code, 200)

    # def test_update_item_kitchen(self):
    #     res = self.client.get(reverse('update_item_kitchen'), follow=True)
    #     self.assertEqual(res.status_code, 200)

    # def test_new_kitchen_item(self):
    #     res = self.client.get(reverse('new_kitchen_item'), follow=True)
    #     self.assertEqual(res.status_code, 200)

    # def test_create_postit(self):
    #     res = self.client.get(reverse('create_postit'), follow=True)
    #     self.assertEqual(res.status_code, 200)

    # def test_edit_postit(self):
    #     res = self.client.get(reverse('edit_postit'), follow=True)
    #     self.assertEqual(res.status_code, 200)

    # def test_delete_postit(self):
    #     res = self.client.get(reverse('delete_postit'), follow=True)
    #     self.assertEqual(res.status_code, 200)

    # def test_search_products_api(self):
    #     res = self.client.get(reverse('search_products_api'), follow=True)
    #     self.assertEqual(res.status_code, 200)

    # def test_check_product_exists_api(self):
    #     res = self.client.get(reverse('check_product_exists_api'), follow=True)
    #     self.assertEqual(res.status_code, 200)


    def test_flow_new_kitchen(self):
        username = f"test-user-tmp-{uuid.uuid4()}"
        email = "tmpuser@testdomain.test"
        password = "testing321"
        self.client.post(reverse('signup'), {
            "username": username,
            "email": email,
            "password1": password,
            "password2": password
        }, follow=True)
        self.client.post(reverse("login"), {
            "username": username,
            "password": password
        }, follow=True)

        try:
            u:User = User.objects.get(username=username)
        except User.DoesNotExist:
            u = None

        username_2 = f"test-user-tmp-{uuid.uuid4()}"
        email_2 = "tmpuser@testdomain.test"
        password_2 = "testing321"
        self.client.post(reverse('signup'), {
            "username": username_2,
            "email": email_2,
            "password1": password_2,
            "password2": password_2
        }, follow=True)
        
        try:
            u2:User = User.objects.get(username=username_2)
        except User.DoesNotExist:
            u2 = None

        get_new_kitchen = self.client.get(reverse('new_kitchen'))
        bad_post_new_kitchen = self.client.post(reverse('new_kitchen'), {
            "invalid-data": "value"
        })
        kitchen_name = f"{username}-test-kitchen"
        good_post_new_kitchen = self.client.post(reverse('new_kitchen'), {
            "name": kitchen_name,
            "invite_other_users": username_2
        }, follow=True)

        try:
            k:Kitchen = Kitchen.objects.get(name=kitchen_name)
        except Kitchen.DoesNotExist:
            k = None

        try:
            m:Membership = Membership.objects.get(kitchen=k, user=u)
        except Kitchen.DoesNotExist:
            m = None

        try:
            m2:Membership = Membership.objects.get(kitchen=k, user=u2)
        except Kitchen.DoesNotExist:
            m2 = None


        # database cleanup
        objects = [u, u2, m, m2, k]
        # for obj in objects:
        #     print(type(obj), obj)
        for obj in objects:
            if obj:
                obj.delete()

        # tests

        self.assertEqual(get_new_kitchen.status_code, 200)
        self.assertEqual(bad_post_new_kitchen.status_code, 400)
        self.assertEqual(good_post_new_kitchen.status_code, 200)

        self.assertIsNotNone(m)
        self.assertEqual(m.status, MembershipStatus.ACTIVE_MEMBERSHIP)
        self.assertTrue(m.is_admin)
        self.assertEqual(m2.status, MembershipStatus.PENDING_INVITATION)
        self.assertFalse(m2.is_admin)

        self.assertIsNotNone(u)
        self.assertEqual(u.username, username)
        self.assertEqual(u.email, email)

        self.assertIsNotNone(u2)
        self.assertEqual(u2.username, username_2)
        self.assertEqual(u2.email, email_2)
        
        self.assertIsNotNone(k)
        self.assertEqual(k.name, kitchen_name)