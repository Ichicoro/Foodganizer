import json
from django.core.exceptions import ObjectDoesNotExist

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.fields.related import ForeignKey, ManyToManyField


def _getLastUpdate():
    return models.DateTimeField(auto_now=True)
    
def _getCreatedAt():
    return models.DateTimeField(auto_now_add=True)

def _getProductQuantity():
    # from 0 to 32767 https://docs.djangoproject.com/en/3.2/ref/models/fields/#positivesmallintegerfield
    return  models.PositiveSmallIntegerField(null=True, default=None) 

def _getAddedBy():
    return models.ForeignKey('User', on_delete=models.SET_NULL, null=True)

def _getLastEditedBy(related_name=None):
    return models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name=related_name)

def _getKitchenForeignKey():
    return models.ForeignKey('Kitchen', on_delete=models.CASCADE)  # class Kitchen is not defined yet, must use a string

def _getItemForeignKey():
    return models.ForeignKey('Item', on_delete=models.PROTECT)  # class Kitchen is not defined yet, must use a string


class User(AbstractUser):
    bio = models.TextField(max_length=1000, blank=True)
    profile_pic = models.ImageField(upload_to='profile_images', blank=True)

    def is_member_of(self, k):
        try:
            m = self.membership_set.get(kitchen=k)
            return m in [MembershipStatus.ACTIVE_MEMBERSHIP, MembershipStatus.ADMIN]
        except ObjectDoesNotExist:
            return False

    def is_admin_of(self, k):
        try:
            m = self.membership_set.get(kitchen=k)
            return m == MembershipStatus.ADMIN
        except ObjectDoesNotExist:
            return False


class Item(models.Model):
    upc = models.CharField(max_length=13, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=500, blank=True)
    image = models.ImageField(upload_to='item_images', blank=True)
    added_by = _getAddedBy()
    last_update = _getLastUpdate()
    created_at = _getCreatedAt()
    custom_item_kitchen = models.ForeignKey('Kitchen', on_delete=models.CASCADE, null=True, default=None) 

    def __str__(self):
        name = self.title
        print(self.upc)
        if self.upc and self.upc not in ["undefined", ""]:
            name = f"{name} (UPC: {self.upc})"
        return name
 

class StoredItem(models.Model):
    item = _getItemForeignKey()
    kitchen = _getKitchenForeignKey()
    added_by = _getAddedBy()
    last_update = _getLastUpdate()
    created_at = _getCreatedAt()
    quantity = _getProductQuantity()
    expiry_date = models.DateField(null=True, default=None, blank=True)
    note = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return f"{self.item}"

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)


class Kitchen(models.Model):
    name = models.CharField(max_length=255)
    # need related_name for backward link https://stackoverflow.com/questions/2606194/django-error-message-add-a-related-name-argument-to-the-definition/44398542
    users = ManyToManyField(User, through='Membership', through_fields=('kitchen', 'user'))
    stored_items = ManyToManyField(Item, through='StoredItem', blank=True)
    public_access_uuid = models.UUIDField(null=True, default=None)
    join_confirmation = models.BooleanField(default=False)
    background_image = models.ImageField(upload_to='backgrounds', blank=True)

    def __str__(self):
        return self.name


class MembershipStatus(models.TextChoices):
    PENDING_JOIN_REQUEST = 'PENDING_JOIN_REQUEST'
    PENDING_INVITATION = 'PENDING_INVITATION'
    ACTIVE_MEMBERSHIP = 'ACTIVE_MEMBERSHIP'
    ADMIN = "ADMIN"


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kitchen = _getKitchenForeignKey()
    status = models.CharField(
        max_length=30,
        choices=MembershipStatus.choices
    )
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, default=None, null=True, related_name="invites_set")

    def __str__(self):
        if self.status == MembershipStatus.PENDING_INVITATION:
            message = f"@{self.invited_by} invited @{self.user} in {self.kitchen}" 
        elif self.status == MembershipStatus.PENDING_JOIN_REQUEST:
            message = f"@{self.user} requested to join {self.kitchen}" 
        elif self.status == MembershipStatus.ACTIVE_MEMBERSHIP:
            message = f"@{self.user} member of {self.kitchen}" 
        elif self.status == MembershipStatus.ADMIN:
            message = f"@{self.user} admin of {self.kitchen}" 
        else:
            message = f"@{self.user} > {self.status} > {self.kitchen}" 

        return message

    class Meta:
        unique_together = [['user', 'kitchen']]
        

class PostIt(models.Model):
    text = models.TextField(max_length=1000)
    author = _getAddedBy()
    last_edited_by = _getLastEditedBy('+')
    kitchen = _getKitchenForeignKey()
    last_update = _getLastUpdate()
    created_at = _getCreatedAt()


class ShoppingCartItem(models.Model):
    kitchen = _getKitchenForeignKey()
    item = _getItemForeignKey()
    added_by = _getAddedBy()
    quantity = _getProductQuantity()
    last_update = _getLastUpdate()
    created_at = _getCreatedAt()

    def __str__(self):
        return f"{self.quantity}x {self.item}"
