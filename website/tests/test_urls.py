import uuid

from django.contrib import auth
from django.contrib.auth.models import AnonymousUser, UserManager
from website.views import kitchen, shared_kitchen

from django.db.models.fields import EmailField
from django.test.testcases import TestCase

from website.models import Kitchen, Membership, MembershipStatus, User
from django.test import SimpleTestCase
from django.urls import reverse, resolve



class TestUrls(TestCase):
    def setUp(self):
        self.username = f"test-user-tmp-{uuid.uuid4()}"
        self.email = "tmpuser@testdomain.test"
        self.password = "testing321"

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

    def _assertUser(self, _u, username, email):
        self.assertFalse(isinstance(_u, AnonymousUser))
        self.assertIsNotNone(_u)
        self.assertEqual(_u.username, username)
        self.assertEqual(_u.email, email)

    def _assertLoggedUser(self, username, email):
        u = auth.get_user(self.client)
        self._assertUser(u, username, email)
    
    def _assertLoggedUserAnon(self):
        u = auth.get_user(self.client)
        self.assertTrue(isinstance(u, AnonymousUser))

    def _assertKitchen(self, k_name):
        k = self._getKitchenByName(k_name)
        self.assertIsNotNone(k)

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

    def test_signup_get_ok(self):
        res = self.client.get(reverse('signup'))
        self.assertEqual(res.status_code, 200)

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
        self.assertEqual(res.status_code, 400)
        _u = self._getUserByUsername(self.username)
        self.assertIsNone(_u)

    def test_signup_post_missing_email(self):
        res = self.client.post(reverse('signup'), {
            "username": self.username,
            "password1": self.password,
            "password2": self.password
        })
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
        self.assertEqual(res.status_code, 400)

    def test_login_get_ok(self):
        res = self.client.get(reverse('login'))
        self.assertEqual(res.status_code, 200)

    def test_login_post_ok(self):
        User.objects.create_user(self.username, self.email, self.password)
        self._assertLoggedUserAnon()
        self.client.post(reverse("login"), {
            "username": self.username,
            "password": self.password
        })
        self._assertLoggedUser(self.username, self.email)
    
    def test_login_post_wrong_user(self):
        User.objects.create_user(self.username, self.email, self.password)
        self.client.post(reverse("login"), {
            "username": self.username+"-test",
            "password": self.password
        })
        self._assertLoggedUserAnon()

    def test_login_post_wrong_password(self):
        User.objects.create_user(self.username, self.email, self.password)
        self.client.post(reverse("login"), {
            "username": self.username,
            "password": "totally-wrong-password"
        })
        self._assertLoggedUserAnon()
        
    def test_profile_get_ok(self):
        u = User.objects.create_user(self.username, self.email, self.password)
        self._login(self.username, self.password)
        res = self.client.get(reverse('profile'))
        self.assertEqual(res.status_code, 200)

    def test_profile_get_anon_user(self):   
        res = self.client.get(reverse('profile'))
        self.assertEqual(res.status_code, 302)

    def test_otherprofile_get_ok(self):
        u = User.objects.create_user(self.username, self.email, self.password)
        res = self.client.get(reverse('otherprofile', args=[u.username]))
        self.assertEqual(res.status_code, 200)
        
    def test_otherprofile_get_wrong_username(self):   
        res = self.client.get(reverse('otherprofile', args=["wrong_username"]), follow=True)
        self.assertEqual(res.status_code, 404)

    def test_logout_get_ok(self):
        u = User.objects.create_user(self.username, self.email, self.password)
        self.client.force_login(u)
        self.client.get(reverse('logout'))
        self._assertLoggedUserAnon()

    def test_kitchens_get_ok(self):
        u = User.objects.create_user(self.username, self.email, self.password)
        self.client.force_login(u)
        res = self.client.get(reverse('kitchens'))
        self.assertEqual(res.status_code, 200)

    def test_new_kitchen_get_ok(self):
        u = User.objects.create_user(self.username, self.email, self.password)
        self.client.force_login(u)
        res = self.client.get(reverse('new_kitchen'))
        self.assertEqual(res.status_code, 200)

    def test_new_kitchen_post_ok(self):
        u1:User = User.objects.create_user(self.username, self.email, self.password)
        u2:User = User.objects.create_user("friend-of-"+self.username, "friend-of-"+self.email, self.password)
        self.client.force_login(u1)
        name = f"{u1.username}-test-kitchen"
        res = self.client.post(reverse('new_kitchen'), {
            "name": name,
            "invite_other_users": u2.username
        })
        self.assertEqual(res.status_code, 302)
        self._assertKitchen(name)
        self._assertMembership(u1, name, MembershipStatus.ACTIVE_MEMBERSHIP)
        self._assertMembership(u2, name, MembershipStatus.PENDING_INVITATION)


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