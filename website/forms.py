from crispy_forms.layout import Field

from .models import Item, Kitchen, User, StoredItem
from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


## CUSTOM FIELDS ##

class MultiUserField(forms.Field):
    def to_python(self, value):
        """Normalize data to a list of strings."""
        # Return an empty list if no input was given.
        if not value:
            return []
        
        contacts = value.replace(";", " ").replace(",", " ").split()
        users = []
        data = []
        for c in contacts:
            try:
                validate_email(c)
                try:
                    u = User.objects.get(email=c)
                except User.DoesNotExist:
                    u = None
                if u not in users:
                    users.append(u)
                    data.append({"value": c, "is_email": True, "User": u})
            except ValidationError:
                try:                            
                    u = User.objects.get(username=c)
                except User.DoesNotExist:                
                    u = None                                
                if c.startswith('@'):
                    c = c[1:]
                if u not in users:
                    users.append(u)    
                    data.append({"value": c, "is_email": False, "User": u})
        return data

    def validate(self, value):
        super().validate(value)
        incorrect_emails = []
        incorrect_usernames = []
        for c in value:
            if not c["User"]:
                if c["is_email"]:
                    incorrect_emails.append(c["value"])
                else:
                    incorrect_usernames.append(c["value"])
                
        error_messages = []

        for ie in incorrect_emails:
            error_messages.append(f"{ie}: We couldn't find a user with this email address")
        
        for iu in incorrect_usernames:
            error_messages.append(f"@{iu}: We couldn't find a user with this username")

        if error_messages:
            raise ValidationError("\n".join(error_messages))



            # if (len(incorrect_emails) == 1):  
            #     raise ValidationError(f"{incorrect_emails[0]} is not a valid email address")
            # else:  
            #     incorrect_emails = ", ".join(incorrect_emails)
            #     raise ValidationError(f"{incorrect_emails} are not valid email addresses")







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
    invite_other_users = MultiUserField(widget=forms.Textarea, required=False)

    class Meta:
        model = Kitchen
        fields = ['name', 'invite_other_users']


class NewKitchenItemForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewKitchenItemForm, self).__init__(*args, **kwargs)
        self.fields['upc'].label = "EAN-13 / UPC"

    upc = forms.CharField(max_length=12, required=False)

    class Meta:
        model = Item
        fields = ['upc', 'title', 'description', 'image']


class AddStoredItemForm(ModelForm):
    Field('item', type="hidden")

    class Meta:
        model = StoredItem
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'})
        }
        fields = ['item', 'quantity', 'expiry_date', 'note']


class RemoveStoredItemForm(forms.Form):
    def __init__(self, *args, **kwargs):
        item_set = kwargs.pop('item_set')
        super(RemoveStoredItemForm, self).__init__(*args, **kwargs)
        self.fields['item'].queryset = item_set

    Field('item', type="hidden")

    item = forms.ModelChoiceField(queryset=None, required=True)
    add_to_shopping_list = forms.BooleanField(required=False)


class UpdateStoredItemForm(ModelForm):
    Field('quantity', type="hidden")

    class Meta:
        model = StoredItem
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'min': 1})
        }
        fields = ['quantity', 'note', 'expiry_date']


class InviteExistingUsers(forms.Form):
    invite_other_users = MultiUserField(widget=forms.Textarea, required=False)
