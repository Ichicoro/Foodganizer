from .models import User
from django.forms import ModelForm
from django import forms


class UpdateUserForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio', 'profile_pic']
