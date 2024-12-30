from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils import timezone
from django_jalali.db import models as jmodels


class User(AbstractBaseUser, PermissionsMixin):
    class UserRoleChoices(models.TextChoices):
        NORMAL = 'normal', 'عادی'
        SCANNER = 'scanner', 'اسکنر'
        KIOSK = 'kiosk', 'کیوسک'

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(_("username"),max_length=150,unique=True,help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."),validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    nationality_id = models.CharField(max_length=10, unique=True, verbose_name="کد ملی/اتباع", null=True, blank=True)
    phone_number = models.CharField(max_length=11, unique=True, verbose_name="شماره تلفن", null=True, blank=True)  
    date_of_birth = jmodels.jDateField(null=True, blank=True, verbose_name="تاریخ تولد")      
    email = models.EmailField(_("email address"), blank=True, null=True)


    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    update = models.DateTimeField(auto_now=True, verbose_name=_('زمان ویرایش'))
    role_info = """
    |عادی :‌ دسترسی به کل بخش های سایت|
    |کیوسک :‌ این دسترسی برای فروش از طریق ماشین تیکت تعریف شده|
    |اسکنر :‌ برای کارکنانی که وظیفه اسکن بارکد را دارند|
    """
    role = models.CharField(verbose_name='نقش کاربری', max_length=10, choices=UserRoleChoices.choices, default=UserRoleChoices.NORMAL, help_text=role_info)
    categories = models.ManyToManyField('Amusement_Park_Application.Category', related_name='users', verbose_name='دسته بندی')

    # Add custom related names to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',  # Unique related_name
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',  # Unique related_name
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_(
            "Specific permissions for this user."
        ),
        related_query_name="user",
    )

    objects = UserManager()

    USERNAME_FIELD = "username"

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ('-update',)

    def clean(self):
        super().clean()

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def __str__(self):
        return f'{self.get_full_name()}'

    def get_categories(self):
        return "\n,".join([c.title for c in self.categories.all()])
