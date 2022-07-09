from PIL import Image
from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    # Attributes of profile

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    source = models.IntegerField(choices=[
        (1, 'IEX Finance'),
        (2, 'Yahoo! Finance'),
    ], default=2)

    iex_api_version = models.CharField(max_length=200, blank=True, null=True, default='iexcloud-sandbox')
    iex_token = models.CharField(max_length=200, blank=True, null=True, default='Tsk_168e230b98fb405684f5be87790ba33b')

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)
