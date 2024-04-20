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


class TableManager(models.Manager):
    use_in_migrations = True

    def create_table(self, email, table_name):
        table = self.model(
            email=email,
            table_name=table_name,
        )
        table.save(using=self._db)
        return table


class Table(models.Model):
    email = models.ForeignKey(User, related_name='table', on_delete=models.PROTECT)
    table_name = models.CharField(max_length=10, default=None, null=True)

    objects = TableManager()

    class Meta:
        db_table = 'table'


class OrderManager(models.Manager):
    use_in_migrations = True

    def create_order(self, table_id, email, menu_id, timestamp, quantity, state):
        order = self.model(
            table_id=table_id,
            email=email,
            menu_id=menu_id,
            timestamp=timestamp,
            quantity=quantity,
            state=state,
        )
        order.save(using=self._db)
        return order


class Order(models.Model):
    table_id = models.ForeignKey(Table, related_name='order', on_delete=models.PROTECT)
    email = models.ForeignKey(User, related_name='order', on_delete=models.PROTECT)
    menu_id = models.ForeignKey(BoothMenu, related_name='order', on_delete=models.PROTECT)
    timestamp = models.DateTimeField(primary_key=True, null=False, blank=False)
    quantity = models.PositiveIntegerField(max_length=1000, null=False, blank=False)
    state = models.CharField(max_length=10, null=False, blank=False)

    objects = OrderManager()

    class Meta:
        db_table = 'order'
