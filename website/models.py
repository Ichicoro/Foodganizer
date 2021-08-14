from django.db import models

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    bio = models.TextField(max_length=1000, blank=True)
    profile_pic = models.ImageField(upload_to='profile_images', blank=True)
