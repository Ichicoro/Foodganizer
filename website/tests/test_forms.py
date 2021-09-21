
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