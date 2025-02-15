from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils import timezone
from django_jalali.db import models as jmodels
from django.core.exceptions import ValidationError


# Define the custom User model extending AbstractBaseUser and PermissionsMixin
class User(AbstractBaseUser, PermissionsMixin):
    # Enum for user roles with custom Persian choices
    class UserRoleChoices(models.TextChoices):
        NORMAL = 'normal', 'دسترسی آزاد'
        SCANNER = 'scanner', 'اسکنر'
        KIOSK = 'kiosk', 'کیوسک'

    # Validator for the username
    username_validator = UnicodeUsernameValidator()

    # Username field with custom validation and error messages
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    
    # Personal information fields
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    nationality_id = models.CharField(max_length=10, unique=True, verbose_name="کد ملی/اتباع", null=True, blank=True)
    phone_number = models.CharField(max_length=11, unique=True, verbose_name="شماره تلفن", null=True, blank=True)  
    date_of_birth = jmodels.jDateField(null=True, blank=True, verbose_name="تاریخ تولد")      
    email = models.EmailField(_("email address"), blank=True, null=True)

    # User status fields
    is_active = models.BooleanField(
        verbose_name="فعال",  # Direct string for verbose name
        default=True,
        help_text="بجای حذف کاربر کافی است تیک این فیلد را بردارید تا این کاربر دیگر هیچ نوع دسترسی ای به وب اپلیکیشن نداشته باشد .",
    )
    
    is_staff = models.BooleanField(
        verbose_name="کارمند",  # Direct string for verbose name
        default=True,
        help_text="این فیلد نشان می‌دهد که آیا کاربر باید به عنوان کارمند فعالیت کند (اخطار : به کاربران کیوسک و اسکنر این دسترسی را ندهید)",  # Direct string for help text
    )
    
    is_superuser = models.BooleanField(
        verbose_name="ادمین",  # Direct string for verbose name
        default=False,
        help_text="این فیلد نشان می‌دهد که آیا کاربر دسترسی کامل به تمامی بخش هارا دارد یا خیر. (اخطار : به کاربران کیوسک و اسکنر این دسترسی را ندهید)",
    )
    
    # Tracking fields for user creation and updates
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    update = models.DateTimeField(auto_now=True, verbose_name=_('زمان ویرایش'))

    # Role description with possible choices
    role_info = """
    عادی :‌ دسترسی به کل بخش های سایت*****
    *****کیوسک :‌ این دسترسی برای فروش از طریق ماشین تیکت تعریف شده*****
    *****اسکنر :‌ برای کارکنانی که وظیفه اسکن بارکد را دارند
    """
    role = models.CharField(
        verbose_name='نقش کاربری',
        max_length=10,
        choices=UserRoleChoices.choices,
        default=UserRoleChoices.NORMAL,
        help_text=role_info
    )

    # Relationship to categories
    categories = models.ManyToManyField('Amusement_Park_Application.Category', related_name='users', verbose_name='دسته بندی')

    # Groups the user belongs to
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',  # Unique related_name to avoid clashes
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_query_name="user",
    )

    # Specific user permissions
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',  # Unique related_name to avoid clashes
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_(
            "Specific permissions for this user."
        ),
        related_query_name="user",
    )

    # Custom manager for the User model
    objects = UserManager()

    # Define the field to be used as the username
    USERNAME_FIELD = "username"

    # Meta information for ordering and naming the model in the admin
    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ('-update',)

    # Clean method to override the default validation (if needed)
    def clean(self):
        super().clean()
        # Check for UserRoleChoices.NORMAL role
        if self.role == self.UserRoleChoices.NORMAL and not (self.is_staff or self.is_superuser):
            raise ValidationError("یک کاربر با دسترسی آزاد باید به پنل کارمند یا ادمین دسترسی داشته باشد.")
        
        # Check for UserRoleChoices.SCANNER and UserRoleChoices.KIOSK roles
        if self.role in [self.UserRoleChoices.SCANNER, self.UserRoleChoices.KIOSK] and (self.is_staff or self.is_superuser):
            raise ValidationError("یک کاربر اسکنر یا کیوسک نمیتواند به عنوان ادمین یا کارمند فعالیت کند (به دلیل مسائل امنیتی).")

    # Method to get the full name of the user (first + last name)
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    # Method to get the short name for the user (first name only)
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    # String representation of the user object
    def __str__(self):
        return f'{self.get_full_name()}'

    # Method to return categories associated with the user as a string
    def get_categories(self):
        return "\n,".join([c.title for c in self.categories.all()])




