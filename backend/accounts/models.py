from django.db import models

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=email,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, password=None):
        superuser = self.create_user(
            email=email,
            password=password,
        )
        superuser.is_staff = True
        superuser.is_superuser = True
        superuser.is_active = True
        superuser.save(using=self._db)
        return superuser


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=30, unique=True, null=False, blank=False, primary_key=True)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_oath = models.BooleanField(default=False)
    booth_name = models.CharField(max_length=15, default=None, null=True)
    bank_name = models.CharField(max_length=30, default=None, null=True)
    banker_name = models.CharField(max_length=5, default=None, null=True)
    account_number = models.CharField(max_length=30, default=None, null=True)
    booth_image_url = models.URLField(max_length=255, default=None, null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    class Meta:
        db_table = 'user'


class BoothMenuManager(models.Manager):
    use_in_migrations = True

    def create_booth_menu(self, email, category, menu_name, price, description):
        booth_menu = self.model(
            email=email,
            category=category,
            menu_name=menu_name,
            description=description,
            price=price,
        )
        booth_menu.save(using=self._db)
        return booth_menu


class BoothMenu(models.Model):
    email = models.ForeignKey(User, related_name='booth_menu', on_delete=models.PROTECT)
    category = models.CharField(max_length=10, default=None, null=True)
    menu_name = models.CharField(max_length=20, blank=False)
    description = models.CharField(max_length=100, null=True, blank=True)
    price = models.IntegerField(default=0, null=False, blank=False)
    menu_image_url = models.URLField(max_length=255, null=True, blank=True)

    objects = BoothMenuManager()

    class Meta:
        db_table = 'booth_menu'
