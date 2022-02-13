import uuid

from django.contrib import auth
from django.contrib.auth.models import AnonymousUser, UserManager
from website.views import invite_users, kitchen, shared_kitchen

from django.db.models.fields import EmailField
from django.test.testcases import TestCase

from website.models import Item, Kitchen, Membership, MembershipStatus, StoredItem, User
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
        self._assertMembership(u1, k_name, MembershipStatus.ADMIN)
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
  
    def test_kitchen_get_ok(self):
        Membership.objects.create(user=self.user_1, kitchen=self.k_1, status=MembershipStatus.ADMIN)
        self.client.force_login(self.user_1)
        url = reverse("kitchen", args=[self.k_1.id])
        res = self.client.get(url)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)

    def test_kitchen_update_post_ok(self):
        Membership.objects.create(user=self.user_1, kitchen=self.k_1, status=MembershipStatus.ADMIN)
        self.client.force_login(self.user_1)
        url = reverse("kitchen", args=[self.k_1.id])

        newName = "new kitchen name"
        res = self.client.post(url, {
            "name": newName
        }, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["kitchen"].name, newName)

    def test_kitchen_get_no_membership(self):
        self.client.force_login(self.user_1)
        url = reverse("kitchen", args=[self.k_1.id])
        res = self.client.get(url, follow=True)
        self.assertTemplateUsed(res, "pages/kitchens.html")
        self.assertEqual(res.status_code, 200)

    def test_kitchen_invite_users_post_ok(self): 
        Membership.objects.create(user=self.user_1, kitchen=self.k_1, status=MembershipStatus.ADMIN)
        self.client.force_login(self.user_1)
        url = reverse("kitchen_invite_users", args=[self.k_1.id])
        res = self.client.post(url, {
            "invite_other_users": self.user_2.username
        }, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["pending_memberships"][0].user.username, self.user_2.username)
        self.assertEqual(res.context["pending_memberships"][0].status, MembershipStatus.PENDING_INVITATION)
        self._assertMembership(self.user_2, self.k_1.name, MembershipStatus.PENDING_INVITATION)
        
    def test_kitchen_invite_users_post_invalid_user(self):
        Membership.objects.create(user=self.user_1, kitchen=self.k_1, status=MembershipStatus.ADMIN)
        self.client.force_login(self.user_1)
        url = reverse("kitchen_invite_users", args=[self.k_1.id])
        invite_other_users = f"{self.user_2.username}, user_wrong_username"
        res = self.client.post(url, {
            "invite_other_users": invite_other_users
        })
        self.assertEqual(res.status_code, 302)
        data = self.client.session.get("invite_existing_users_form__invite_other_users")
        self.assertIsNotNone(data)
        self.assertEqual(data, invite_other_users)

    def test_join_kitchen_post_ok(self):
        Membership.objects.create(user=self.user_1, kitchen=self.k_1, status=MembershipStatus.PENDING_INVITATION)
        self.client.force_login(self.user_1)
        url = reverse("join_kitchen", args=[self.k_1.id])
        res = self.client.post(url, follow=True)
        self.assertTemplateUsed(res, "pages/kitchens.html")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["active_memberships"][0].user.username, self.user_1.username)
        self.assertEqual(res.context["active_memberships"][0].status, MembershipStatus.ACTIVE_MEMBERSHIP)
        self._assertMembership(self.user_1, self.k_1.name, MembershipStatus.ACTIVE_MEMBERSHIP)

    def test_remove_user_from_kitchen_post_ok(self):
        Membership.objects.create(user=self.user_1, kitchen=self.k_1, status=MembershipStatus.ADMIN)
        m2: Membership = Membership.objects.create(user=self.user_2, kitchen=self.k_1, status=MembershipStatus.ACTIVE_MEMBERSHIP)
        self.client.force_login(self.user_1)
        
        url = reverse("delete_membership", args=[m2.id])
        res = self.client.post(url, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context["memberships"]), 1)
        self.assertEqual(res.context["memberships"][0].user.username, self.user_1.username)

    def test_create_item_post_ok(self):
        Membership.objects.create(user=self.user_1, kitchen=self.k_1, status=MembershipStatus.ACTIVE_MEMBERSHIP)
        self.client.force_login(self.user_1)
        url = reverse("new_kitchen_item", args=[self.k_1.id])
        upc = "3344556677889"
        title = "test item from barcode"
        res = self.client.post(url, {
            'upc': upc,
            'title': title
        }, follow=True)
        self.assertTemplateUsed(res, "pages/add-item-kitchen.html")
        self.assertEqual(res.status_code, 200)
        item_list = Item.objects.filter(upc=upc)
        self.assertEqual(len(item_list), 1)
        self.assertEqual(item_list[0].title, title)

    def test_create_custom_item_post_ok(self):
        Membership.objects.create(user=self.user_1, kitchen=self.k_1, status=MembershipStatus.ACTIVE_MEMBERSHIP)
        self.client.force_login(self.user_1)
        url = reverse("new_kitchen_item", args=[self.k_1.id])
        title = "test custom item"
        res = self.client.post(url, {
            'upc': "",
            'title': title,
            'custom_item_kitchen': self.k_1.id
        }, follow=True)
        self.assertTemplateUsed(res, "pages/add-item-kitchen.html")
        self.assertEqual(res.status_code, 200)
        item_list = Item.objects.filter(custom_item_kitchen=self.k_1)
        self.assertEqual(len(item_list), 1)
        self.assertEqual(item_list[0].title, title)

    def test_add_item_post_ok(self):
        Membership.objects.create(user=self.user_1, kitchen=self.k_1, status=MembershipStatus.ACTIVE_MEMBERSHIP)
        self.client.force_login(self.user_1)
        i: Item = Item.objects.create(id=123, title="test product", upc="123123123123")
        url = reverse("add_storeditem_kitchen", args=[self.k_1.id])
        res = self.client.post(url, {
            'item': i.id,
            'quantity': 3
        }, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['stored_items']), 1)
        self.assertEqual(res.context['stored_items'][0].item.id, i.id)
        self.assertEqual(res.context['stored_items'][0].quantity, 3)

    def test_add_custom_item_post_ok(self):
        Membership.objects.create(user=self.user_1, kitchen=self.k_1, status=MembershipStatus.ACTIVE_MEMBERSHIP)
        self.client.force_login(self.user_1)
        i: Item = Item.objects.create(id=123, title="custom test product", custom_item_kitchen=self.k_1)
        url = reverse("add_storeditem_kitchen", args=[self.k_1.id])
        res = self.client.post(url, {
            'item': i.id,
            'quantity': 5
        }, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['stored_items']), 1)
        self.assertEqual(res.context['stored_items'][0].item.id, i.id)
        self.assertEqual(res.context['stored_items'][0].quantity, 5)

    def test_edit_item_post_ok(self):
        Membership.objects.create(user=self.user_1, kitchen=self.k_1, status=MembershipStatus.ACTIVE_MEMBERSHIP)
        self.client.force_login(self.user_1)
        i: Item = Item.objects.create(id=444, title="test product", upc="123123123123")
        si: StoredItem = StoredItem.objects.create(id=555, item=i, kitchen=self.k_1, quantity=10)
        url = reverse("update_storeditem_kitchen", args=[self.k_1.id, si.id])
        res = self.client.post(url, {
            'quantity': 100
        }, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['stored_items']), 1)
        self.assertEqual(res.context['stored_items'][0].id, si.id)
        self.assertEqual(res.context['stored_items'][0].item.id, i.id)
        self.assertEqual(res.context['stored_items'][0].quantity, 100)

    def test_edit_custom_item_post_ok(self):
        Membership.objects.create(user=self.user_1, kitchen=self.k_1, status=MembershipStatus.ACTIVE_MEMBERSHIP)
        self.client.force_login(self.user_1)
        i: Item = Item.objects.create(id=99, title="custom test product", custom_item_kitchen=self.k_1)
        si: StoredItem = StoredItem.objects.create(id=555, item=i, kitchen=self.k_1, quantity=10)
        url = reverse("update_storeditem_kitchen", args=[self.k_1.id, si.id])
        res = self.client.post(url, {
            'quantity': 44
        }, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['stored_items']), 1)
        self.assertEqual(res.context['stored_items'][0].id, si.id)
        self.assertEqual(res.context['stored_items'][0].item.id, i.id)
        self.assertEqual(res.context['stored_items'][0].quantity, 44)

    def test_remove_item_post_ok(self):
        Membership.objects.create(user=self.user_1, kitchen=self.k_1, status=MembershipStatus.ACTIVE_MEMBERSHIP)
        self.client.force_login(self.user_1)
        i: Item = Item.objects.create(id=333, title="test product", upc="123123123123")
        si: StoredItem = StoredItem.objects.create(id=222, item=i, kitchen=self.k_1)
        url = reverse("delete_storeditem_kitchen", args=[self.k_1.id])
        res = self.client.post(url, {
            'item': si.id
        }, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['stored_items']), 0)

    def test_remove_custom_item_post_ok(self):
        Membership.objects.create(user=self.user_1, kitchen=self.k_1, status=MembershipStatus.ACTIVE_MEMBERSHIP)
        self.client.force_login(self.user_1)
        i: Item = Item.objects.create(id=345, title="custom test product", custom_item_kitchen=self.k_1)
        si: StoredItem = StoredItem.objects.create(id=123, item=i, kitchen=self.k_1)
        url = reverse("delete_storeditem_kitchen", args=[self.k_1.id])
        res = self.client.post(url, {
            'item': si.id
        }, follow=True)
        self.assertTemplateUsed(res, "pages/kitchen.html")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['stored_items']), 0)
