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

def _getKitchenForeignKey():
    return models.ForeignKey('Kitchen', on_delete=models.CASCADE)  # class Kitchen is not defined yet, must use a string

def _getItemForeignKey():
    return models.ForeignKey('Item', on_delete=models.PROTECT)  # class Kitchen is not defined yet, must use a string


class User(AbstractUser):
    bio = models.TextField(max_length=1000, blank=True)
    profile_pic = models.ImageField(upload_to='profile_images', blank=True)

class Item(models.Model):
    upc = models.CharField(max_length=12) 
    # TODO: create form validation for integer only https://stackoverflow.com/questions/60966095/django-charfield-accepting-only-numbers
    # TODO: accept only upc_a or upc_e https://en.wikipedia.org/wiki/Universal_Product_Code
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=500, blank=True)
    image = models.ImageField(upload_to='item_images', blank=True)
    added_by = _getAddedBy()
    last_update = _getLastUpdate()
    created_at = _getCreatedAt()
    kitchen = _getKitchenForeignKey()

class StoredItem(models.Model):
    item = _getItemForeignKey()
    added_by = _getAddedBy()
    last_update = _getLastUpdate()
    created_at = _getCreatedAt()
    quantity = _getProductQuantity()
    expiry_date = models.DateField(null=True, default=None)
    note = models.TextField(max_length=500, blank=True)

class Kitchen(models.Model):
    # need related_name for backward link https://stackoverflow.com/questions/2606194/django-error-message-add-a-related-name-argument-to-the-definition/44398542
    users = ManyToManyField(User, related_name="kitchen_users")
    admins = ManyToManyField(User, related_name="kitchen_admins") # TODO: are admins inside users list?
    stored_items = ManyToManyField(StoredItem)

class PostIt(models.Model):
    text = models.TextField(max_length=1000)
    author = _getAddedBy()
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
    