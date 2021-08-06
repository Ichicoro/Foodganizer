from django.contrib.auth.models import User
from .models import Profile
from django.forms import ModelForm
from django import forms


class UpdateUserForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class UpdateProfileForm(ModelForm):
    bio = forms.CharField(max_length=500, required=False)
    birth_date = forms.DateField(required=False)

    class Meta:
        model = Profile
        fields = ['bio', 'birth_date']
