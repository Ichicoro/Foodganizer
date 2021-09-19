import uuid

from django.contrib import auth
from django.contrib.auth.models import AnonymousUser, UserManager
from website.views import kitchen, shared_kitchen

from django.db.models.fields import EmailField
from django.test.testcases import TestCase

from website.models import Kitchen, Membership, MembershipStatus, User
from django.test import SimpleTestCase, client
from django.urls import reverse, resolve



class TestViews(TestCase):
    def setUp(self):
        self.username = f"test-user-tmp-{uuid.uuid4()}"
        self.email = "tmpuser@testdomain.test"
        self.password = "testing321"

        self.user_1:User = User.objects.create_user("test-user-1", "user1@test.com", "testing321")
        self.k_1:Kitchen = Kitchen.objects.create(name="test-kitchen-1", public_access_uuid=uuid.uuid4())

        self.user_2:User = User.objects.create_user("test-user-2", "user2@test.com", "testing321")
        self.k_confirm:Kitchen = Kitchen.objects.create(name="test-kitchen-2", public_access_uuid=uuid.uuid4(), join_confirmation=True)
        self.k_no_confirm:Kitchen = Kitchen.objects.create(name="test-kitchen-3", public_access_uuid=uuid.uuid4())
        self.k_confirm_url = reverse("share_kitchen_link", args=[self.k_confirm.public_access_uuid])
        self.k_no_confirm_url = reverse("share_kitchen_link", args=[self.k_no_confirm.public_access_uuid])

    def _getUserByUsername(self, u: str) -> User:
        try:
            return User.objects.get(username=u)
        except User.DoesNotExist:
            return None

    def _getKitchenByName(self, k_name) -> Kitchen:
        try:
            return Kitchen.objects.get(name=k_name)
        except Kitchen.DoesNotExist:
            return None

    def _assertUser(self, _u, username=None, email=None):
        self.assertFalse(isinstance(_u, AnonymousUser))
        self.assertIsNotNone(_u)
        if username:
            self.assertEqual(_u.username, username)
        if email:
            self.assertEqual(_u.email, email)
    
    def _assertNotUser(self, _u):
        self.assertTrue(not _u or isinstance(_u, AnonymousUser))

    def _assertLoggedUser(self, username, email):
        u = auth.get_user(self.client)
        self._assertUser(u, username, email)
    
    def _assertLoggedUserAnon(self):
        u = auth.get_user(self.client)
        self._assertNotUser(u)

    def _assertKitchen(self, k_name):
        k = self._getKitchenByName(k_name)
        self.assertIsNotNone(k)

    def _assertNotKitchen(self, k_name):
        k = self._getKitchenByName(k_name)
        self.assertIsNone(k)

    def _assertMembership(self, u:User, k_name:str, status:MembershipStatus):
        try:
            k = self._getKitchenByName(k_name)
            m: Membership = Membership.objects.get(user=u, kitchen=k)
        except Membership.DoesNotExist:
            m = None
        self.assertIsNotNone(m)
        self.assertEqual(m.status, status)

    def _login(self, username, password):
        self.client.post(reverse("login"), {
            "username": username,
            "password": password
        })

    def test_index_get_ok(self):
        res = self.client.get(reverse('index'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "pages/index.html")

    def test_signup_get_ok(self):
        res = self.client.get(reverse('signup'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed("registration/signup.html")

    def test_signup_post_ok(self):
        res = self.client.post(reverse('signup'), {
            "username": self.username,
            "email": self.email,
            "password1": self.password,
            "password2": self.password
        })
        self.assertEqual(res.status_code, 302)
        _u = self._getUserByUsername(self.username)
        self._assertUser(_u, self.username, self.email)

    def test_signup_post_mismatching_passwords(self):
        res = self.client.post(reverse('signup'), {
            "username": self.username,
            "email": self.email,
            "password1": self.password+"test",
            "password2": self.password
        })
        self.assertTemplateUsed("registration/signup.html")
        self.assertEqual(res.status_code, 400)
        _u = self._getUserByUsername(self.username)
        self._assertNotUser(_u)

    def test_signup_post_missing_email(self):
        res = self.client.post(reverse('signup'), {
            "username": self.username,
            "password1": self.password,
            "password2": self.password
        })
        self.assertTemplateUsed("registration/signup.html")
        self.assertEqual(res.status_code, 400)
        _u = self._getUserByUsername(self.username)
        self.assertIsNone(_u)

    def test_signup_post_existing_user(self):
        User.objects.create_user(self.username, self.email, self.password)
        res = self.client.post(reverse('signup'), {
            "username": self.username,
            "email": self.email,
            "password1": self.password,
            "password2": self.password
        })
        self.assertTemplateUsed("registration/signup.html")
        self.assertEqual(res.status_code, 400)

    def test_login_get_ok(self):
        res = self.client.get(reverse('login'))
        self.assertTemplateUsed("registration/login.html")
        self.assertEqual(res.status_code, 200)

    def test_login_post_ok(self):
        User.objects.create_user(self.username, self.email, self.password)
        res = self.client.post(reverse("login"), {
            "username": self.username,
            "password": self.password
        })
        self.assertEqual(res.status_code, 302)
        self._assertLoggedUser(self.username, self.email)
    
    def test_login_post_wrong_user(self):
        User.objects.create_user(self.username, self.email, self.password)
        res = self.client.post(reverse("login"), {
            "username": self.username+"-testaaa",
            "password": self.password
        })
        self.assertTemplateUsed(res, "registration/login.html")
        # self.assertEqual(res.status_code, 400) TODO: check why res code is 200
        self._assertLoggedUserAnon()

    def test_login_post_wrong_password(self):
        User.objects.create_user(self.username, self.email, self.password)
        res = self.client.post(reverse("login"), {
            "username": self.username,
            "password": "totally-wrong-password"
        })
        self.assertTemplateUsed(res, "registration/login.html")
        # self.assertEqual(res.status_code, 400) TODO: check why res code is 200
        self._assertLoggedUserAnon()
        
    def test_profile_get_ok(self):
        self.client.force_login(self.user_1)
        res = self.client.get(reverse('profile'))
        self.assertTemplateUsed(res, "pages/own_profile.html")
        self.assertEqual(res.status_code, 200)

    def test_profile_get_anon_user(self):   
        res = self.client.get(reverse('profile'))
        self.assertEqual(res.status_code, 302)

    def test_otherprofile_get_ok(self):
        u = User.objects.create_user(self.username, self.email, self.password)
        res = self.client.get(reverse('otherprofile', args=[u.username]))
        self.assertTemplateUsed(res, "pages/view_profile.html")
        self.assertEqual(res.status_code, 200)
        
    def test_otherprofile_get_wrong_username(self):   
        res = self.client.get(reverse('otherprofile', args=["wrong_username"]), follow=True)
        self.assertTemplateUsed(res, "pages/view_profile.html")
        self.assertEqual(res.status_code, 404)

    def test_logout_get_ok(self):
        self.client.force_login(self.user_1)
        res = self.client.get(reverse('logout'))
        self.assertEqual(res.status_code, 302)
        self._assertLoggedUserAnon()

    def test_kitchens_get_ok(self):
        self.client.force_login(self.user_1)
        res = self.client.get(reverse('kitchens'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "pages/kitchens.html")

    def test_new_kitchen_get_ok(self):
        self.client.force_login(self.user_1)
        res = self.client.get(reverse('new_kitchen'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "pages/new-kitchen.html")

    def test_new_kitchen_post_ok(self):
        u1:User = self.user_1
        u2:User = User.objects.create_user("friend-of-"+u1.username, "friend-of-"+u1.email, "testing321")
        self.client.force_login(u1)
        k_name = f"{u1.username}-test-kitchen"
        k_count = Kitchen.objects.count()
        res = self.client.post(reverse('new_kitchen'), {
            "name": k_name,
            "invite_other_users": u2.username
        })
        self.assertEqual(res.status_code, 302)
        self._assertKitchen(k_name)
        self.assertEqual(k_count + 1, Kitchen.objects.count())
        self._assertMembership(u1, k_name, MembershipStatus.ACTIVE_MEMBERSHIP)
        self._assertMembership(u2, k_name, MembershipStatus.PENDING_INVITATION)
    
    def test_new_kitchen_post_invalid_body(self):
        u1:User = self.user_1
        self.client.force_login(u1)
        k_name = f"{u1.username}-test-kitchen"
        k_count = Kitchen.objects.count()
        res = self.client.post(reverse('new_kitchen'), {
            "wrong-param": k_name
        })
        self.assertTemplateUsed(res, "pages/new-kitchen.html")
        self.assertEqual(res.status_code, 400)
        self._assertNotKitchen(k_name)
        self.assertEqual(k_count, Kitchen.objects.count())

    def test_share_kitchen_get_ok(self):
        self.client.force_login(self.user_1)
        url = reverse("share_kitchen_link", args=[self.k_1.public_access_uuid])
        res = self.client.get(url)
        self.assertTemplateUsed(res, "pages/join-shared-kitchen.html")
        self.assertEqual(res.status_code, 200)
    
    def test_share_kitchen_get_not_found(self):
        self.client.force_login(self.user_1)
        url = reverse("share_kitchen_link", args=[uuid.uuid4()])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)
        res = self.client.get(url, follow=True)
        self.assertTemplateUsed(res, "pages/kitchens.html")
        self.assertEqual(res.status_code, 200)

    def test_share_kitchen_post_ok_confirm_without_membership(self):
        self.client.force_login(self.user_2)
        res = self.client.post(self.k_confirm_url, follow=True)
        self.assertTemplateUsed(res, "pages/kitchens.html")
        self.assertEqual(res.status_code, 200)
        self._assertMembership(self.user_2, self.k_confirm.name, MembershipStatus.PENDING_JOIN_REQUEST)

    def test_share_kitchen_post_ok_confirm_with_active_membership(self):
        self.client.force_login(self.user_2)
        self.user_2.membership_set.create(kitchen=self.k_confirm, status=MembershipStatus.ACTIVE_MEMBERSHIP)
        res = self.client.post(self.k_confirm_url, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self._assertMembership(self.user_2, self.k_confirm.name, MembershipStatus.ACTIVE_MEMBERSHIP)

    def test_share_kitchen_post_ok_confirm_with_pending_invitation(self):
        self.client.force_login(self.user_2)
        self.user_2.membership_set.create(kitchen=self.k_confirm, status=MembershipStatus.PENDING_INVITATION)
        res = self.client.post(self.k_confirm_url, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self._assertMembership(self.user_2, self.k_confirm.name, MembershipStatus.ACTIVE_MEMBERSHIP)

    def test_share_kitchen_post_ok_confirm_with_pending_join_request(self):
        self.client.force_login(self.user_2)
        self.user_2.membership_set.create(kitchen=self.k_confirm, status=MembershipStatus.PENDING_JOIN_REQUEST)
        res = self.client.post(self.k_confirm_url, follow=True)
        self.assertTemplateUsed(res, "pages/kitchens.html")
        self.assertEqual(res.status_code, 200)
        self._assertMembership(self.user_2, self.k_confirm.name, MembershipStatus.PENDING_JOIN_REQUEST)

    def test_share_kitchen_post_ok_no_confirm_without_membership(self):
        self.client.force_login(self.user_2)
        res = self.client.post(self.k_no_confirm_url, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self._assertMembership(self.user_2, self.k_no_confirm.name, MembershipStatus.ACTIVE_MEMBERSHIP)

    def test_share_kitchen_post_ok_no_confirm_with_active_membership(self):
        self.client.force_login(self.user_2)
        self.user_2.membership_set.create(kitchen=self.k_no_confirm, status=MembershipStatus.ACTIVE_MEMBERSHIP)
        res = self.client.post(self.k_no_confirm_url, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self._assertMembership(self.user_2, self.k_no_confirm.name, MembershipStatus.ACTIVE_MEMBERSHIP)

    def test_share_kitchen_post_ok_no_confirm_with_pending_invitation(self):
        self.client.force_login(self.user_2)
        self.user_2.membership_set.create(kitchen=self.k_no_confirm, status=MembershipStatus.PENDING_INVITATION)
        res = self.client.post(self.k_no_confirm_url, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self._assertMembership(self.user_2, self.k_no_confirm.name, MembershipStatus.ACTIVE_MEMBERSHIP)

    def test_share_kitchen_post_ok_no_confirm_with_pending_join_request(self):
        self.client.force_login(self.user_2)
        self.user_2.membership_set.create(kitchen=self.k_no_confirm, status=MembershipStatus.PENDING_JOIN_REQUEST)
        res = self.client.post(self.k_no_confirm_url, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self._assertMembership(self.user_2, self.k_no_confirm.name, MembershipStatus.ACTIVE_MEMBERSHIP)
  

    ## TODO: view tests for this urls

    # def test_kitchen_is_resolved(self):
    #     url = reverse("kitchen", args=[123])
    #     self.assertEqual(resolve(url).func, kitchen)
    
    # def test_kitchen_invite_users_is_resolved(self):
    #     url = reverse("kitchen_invite_users", args=[123])
    #     self.assertEqual(resolve(url).func, invite_users)
    
    # def test_delete_membership_is_resolved(self):
    #     url = reverse("delete_membership", args=[123])
    #     self.assertEqual(resolve(url).func, delete_membership)
    
    # def test_set_kitchen_sharing_is_resolved(self):
    #     url = reverse("set_kitchen_sharing", args=[123])
    #     self.assertEqual(resolve(url).func, set_kitchen_sharing)
    
    # def test_join_kitchen_is_resolved(self):
    #     url = reverse("join_kitchen", args=[123])
    #     self.assertEqual(resolve(url).func, join_kitchen)
    
    # def test_add_storeditem_kitchen_is_resolved(self):
    #     url = reverse("add_storeditem_kitchen", args=[123])
    #     self.assertEqual(resolve(url).func, add_storeditem_kitchen)
    
    # def test_delete_storeditem_kitchen_is_resolved(self):
    #     url = reverse("delete_storeditem_kitchen", args=[123])
    #     self.assertEqual(resolve(url).func, delete_storeditem_kitchen)
    
    # def test_update_storeditem_kitchen_is_resolved(self):
    #     url = reverse("update_storeditem_kitchen", args=[123, 456])
    #     self.assertEqual(resolve(url).func, update_storeditem_kitchen)
    
    # def test_add_cartitem_kitchen_is_resolved(self):
    #     url = reverse("add_cartitem_kitchen", args=[123])
    #     self.assertEqual(resolve(url).func, add_cartitem_kitchen)
    
    # def test_update_cartitem_kitchen_is_resolved(self):
    #     url = reverse("update_cartitem_kitchen", args=[123, 456])
    #     self.assertEqual(resolve(url).func, update_cartitem_kitchen)
    
    # def test_delete_cartitem_kitchen_is_resolved(self):
    #     url = reverse("delete_cartitem_kitchen", args=[123, 456])
    #     self.assertEqual(resolve(url).func, delete_cartitem_kitchen)
    
    # def test_new_kitchen_item_is_resolved(self):
    #     url = reverse("new_kitchen_item", args=[123])
    #     self.assertEqual(resolve(url).func, new_kitchen_item)
    
    # def test_delete_customitem_kitchen_is_resolved(self):
    #     url = reverse("delete_customitem_kitchen", args=[123, 456])
    #     self.assertEqual(resolve(url).func, delete_customitem_kitchen)
    
    # def test_create_postit_is_resolved(self):
    #     url = reverse("create_postit", args=[123])
    #     self.assertEqual(resolve(url).func, create_postit)
    
    # def test_edit_postit_is_resolved(self):
    #     url = reverse("edit_postit", args=[123, 456])
    #     self.assertEqual(resolve(url).func, edit_postit)
    
    # def test_delete_postit_is_resolved(self):
    #     url = reverse("delete_postit", args=[123, 456])
    #     self.assertEqual(resolve(url).func, delete_postit)
    
    # def test_search_products_api_is_resolved(self):
    #     url = reverse("search_products_api")
    #     self.assertEqual(resolve(url).func, search_products)
    
    # def test_check_product_exists_api_is_resolved(self):
    #     url = reverse("check_product_exists_api")
    #     self.assertEqual(resolve(url).func, get_product_by_code)