from django.db import models
from django.contrib.auth.models import User


# Create your models here.


class PassengerProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )

    phone_number = models.CharField(max_length=20, blank=True)
    passport_number = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)


    def __str__(self):
        return f"{self.user.username} Profile"