from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django_jalali.db import models as jmodels


class MyUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        """
        Creates and saves a User with the given username, password, and additional fields.
        """
        if not username:
            raise ValueError("Users must have a username")
        
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given username, password, and additional fields.
        This version ensures that other fields like first_name, last_name, etc., are optional.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        # Optional fields, so they won't be required in the create_superuser command
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(username, password, **extra_fields)


class MyUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Users must have a username")
        
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        return self.create_user(username, password, **extra_fields)

class MyUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=255, unique=True, verbose_name="نام کاربری")
    first_name = models.CharField(max_length=55, verbose_name="نام", null=True, blank=True)
    last_name = models.CharField(max_length=55, verbose_name="نام خانوادگی", null=True, blank=True)
    nationality_id = models.CharField(max_length=10, unique=True, verbose_name="کد ملی", null=True, blank=True)
    phone_number = models.CharField(max_length=11, unique=True, verbose_name="شماره تلفن", null=True, blank=True)
    duty = models.CharField(max_length=55, verbose_name="وظیفه", null=True, blank=True)
    email = models.EmailField(unique=True, verbose_name="آدرس ایمیل", null=True, blank=True)
    date_of_birth = jmodels.jDateField(null=True, blank=True, verbose_name="تاریخ تولد")
    is_active = models.BooleanField(verbose_name="فعال", default=True)
    is_staff = models.BooleanField(verbose_name="کارمند", default=True)
    is_superuser = models.BooleanField(verbose_name="ادمین", default=False, help_text= "به این گزینه دقت کنید زیرا اگر بله را انتخاب کنید این کاربر میتواند به این صفحه دسترسی داشته باشد (نکته :‌ شما میتوانید گروه بندی کنید)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی", null=True, blank=True)

    objects = MyUserManager()
    verbose_name_plural = "آشپز ها"

    USERNAME_FIELD = 'username'
    
    def __str__(self):
        return self.username

    def get_categories(self):
        return "\n,".join([c.title for c in self.categories.all()])
    
    class Meta:
        verbose_name_plural = "کاربر ها"
    
