
from website.models import User
from website.forms import MultiUserField, UpdateUserForm
from django import forms
from django.test.testcases import TestCase
from django.urls import reverse, resolve


class TestForms(TestCase):

    def setUp(self):
        self.users = []
        for i in range(5):
            self.users.append(User.objects.create(username=f"test-user-{i}", email=f"t-u-{i}@testusers.com"))

    def _assertModelForm(self, form, data):
        for key in data.keys():
            self.assertEqual(data[key], form.cleaned_data[key])

    def test_multi_user_field_ok(self):
        class TestForm(forms.Form):
            multi_user_field = MultiUserField()
        
        form = TestForm(data={
            "multi_user_field": "t-u-0@testusers.com\ntest-user-1 test-user-2,,,,t-u-3@testusers.com;  test-user-4"
        })

        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.cleaned_data["multi_user_field"]), 5)
        for i, contact in enumerate(form.cleaned_data["multi_user_field"]):
            self.assertEqual(contact["User"].username, self.users[i].username)
            self.assertEqual(contact["User"].email, self.users[i].email)

    def test_multi_user_field_ok_empty(self):
        class TestForm(forms.Form):
            multi_user_field = MultiUserField()
        
        form = TestForm(data={
            "multi_user_field": ""
        })

        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.cleaned_data["multi_user_field"]), 0)

    def test_multi_user_field_wrong_data(self):
        class TestForm(forms.Form):
            multi_user_field = MultiUserField()
        
        form = TestForm(data={
            "multi_user_field": "wrong-username, wrong@email.com"
        })
        
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)

    
    def test_update_user_form_ok(self):
        data = {
            'first_name': "Test",
            'last_name': "User",
            'email': "new-email-tu0@testusers.com",
            'bio': "i'm a test user",
            # 'profile_pic': TODO: how do i test profile_pic?
        }

        form = UpdateUserForm(data=data, instance=self.users[0])
        self.assertTrue(form.is_valid())
        form.save()
        self._assertModelForm(form, data)

        