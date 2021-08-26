from .models import Item, Kitchen, User
from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


## CUSTOM FIELDS ##

class MultiEmailField(forms.Field):
    def to_python(self, value):
        """Normalize data to a list of strings."""
        # Return an empty list if no input was given.
        if not value:
            return []
        return value.replace(";", " ").replace(",", " ").split()

    def validate(self, value):
        super().validate(value)
        incorrect_emails = []
        for email in value:
            try:
                validate_email(email)
            except ValidationError:
                incorrect_emails.append(email)
        if incorrect_emails: 
            if (len(incorrect_emails) == 1):  
                raise ValidationError(f"{incorrect_emails[0]} is not a valid email address")
            else:  
                incorrect_emails = ", ".join(incorrect_emails)
                raise ValidationError(f"{incorrect_emails} are not valid email addresses")







## FORMS ##

class UpdateUserForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio', 'profile_pic']


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class NewKitchenForm(ModelForm):
    invite_other_users = MultiEmailField(widget=forms.Textarea, required=False)
    class Meta:
        model = Kitchen
        fields = ['name', 'invite_other_users']

class NewKitchenItemForm(ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'description', 'image']