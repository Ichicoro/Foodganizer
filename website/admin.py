from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from website.models import Item, Kitchen, Membership, PostIt, ShoppingCartItem, StoredItem, User

admin.site.register([User, Item, StoredItem, Kitchen, Membership, PostIt, ShoppingCartItem])