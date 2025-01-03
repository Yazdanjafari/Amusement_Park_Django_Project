from collections.abc import Iterable
from django.db import models
from django.contrib.auth import get_user_model
from django.core.cache import cache
import jdatetime
import uuid
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.contrib import messages
from .utils import custom_round_calculate
from .managers import CategoryQuerySet, ProductModelManager
from treebeard.mp_tree import MP_Node
from django_jalali.db import models as jmodels
from datetime import timedelta
from django.utils import timezone

# Category Model: Represents product categories, inheriting from MP_Node for tree structure.
class Category(MP_Node):
    title = models.CharField(max_length=255, db_index=True, verbose_name='عنوان')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    products = models.ManyToManyField('Product', related_name='categories')

    node_order_by = ['title']  # Determines the order of nodes in the tree structure.
    objects = CategoryQuerySet.as_manager()  # Custom manager for category queries.

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "دسته بندی"
        verbose_name_plural = "دسته بندی"

    # Get a list of product titles in this category, formatted as a string.
    def get_products(self):
        return "\n,".join([p.title for p in self.products.all()])


# Product Model: Represents a product in the system.
class Product(models.Model):
    title = models.CharField(max_length=512, verbose_name='نام محصول', unique=True)
    price = models.PositiveBigIntegerField(verbose_name='قیمت')
    tourist_price = models.PositiveBigIntegerField(default=0, verbose_name='قیمت توریستی')
    image = models.ImageField(upload_to='product_image/', verbose_name='تصویر', help_text='سایز 800*800')
    is_active = models.BooleanField(default=True, verbose_name='وضعیت فعال')
    is_taxable = models.BooleanField(default=False, verbose_name='مشمول مالیات بر ارزش افزوده')
    order_metric = models.PositiveIntegerField(editable=False, default=0)

    created = models.DateTimeField(auto_now_add=True, verbose_name=' زمان ایجاد')
    update = models.DateTimeField(auto_now=True, verbose_name=' زمان ویرایش')

    objects = ProductModelManager()  # Custom manager for product queries.

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ('-order_metric',)

    def __str__(self):
        return f'{self.title}'

    # Convert creation time to Jalali date format.
    def j_created(self):
        if self.created:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.created.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''

    # Convert update time to Jalali date format.
    def j_update(self):
        if self.update:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.update.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''


# TaxRate Model: Stores VAT tax rates.
class TaxRate(models.Model):
    rate = models.DecimalField(max_digits=4, decimal_places=2, default=9)

    class Meta:
        verbose_name = "نرخ مالیات بر ارزش افزوده"
        verbose_name_plural = "نرخ مالیات بر ارزش افزوده"

    def __str__(self):
        return str(self.rate)

    # Cache the tax rate.
    def set_cache(self):
        cache.set(self.__class__.__name__, self)

    def save(self, *args, **kwargs):
        self.pk = 1  # Ensures only one instance of this model exists.
        super().save(*args, **kwargs)
        self.set_cache()

    def delete(self, *args, **kwargs):
        pass  # Prevent deletion of the tax rate.

    # Load tax rate from cache, or fetch from database.
    @classmethod
    def load(cls):
        if cache.get(cls.__name__) is None:
            obj, created = cls.objects.get_or_create(pk=1)
            if not created:
                obj.set_cache()
        return cache.get(cls.__name__)


# Transaction Model: Stores transaction details.
class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        pc = ('pc', 'pc pos')
        cash = ('cash', 'نقدی')
        card = ('card', 'کارتی')

    tracking_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    type = models.CharField(max_length=10, choices=TransactionType.choices, verbose_name='نوع تراکنش', default=TransactionType.card)
    is_success = models.BooleanField('تراکنش موفق', default=False)
    price = models.PositiveBigIntegerField(verbose_name='مبلغ تراکنش')
    trans_id = models.CharField(max_length=128, verbose_name='شماره تراکنش', null=True, blank=True)
    date = models.CharField(max_length=128, verbose_name='زمان تراکنش', null=True, blank=True)
    desc = models.TextField('توضیحات', null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name='sale', verbose_name='فروشنده')
    has_tax = models.BooleanField('با احتساب ارزش افزورده', default=False)
    discount = models.PositiveBigIntegerField(default=0, null=True, blank=True, verbose_name='مبلغ تخفیف')
    ticket = models.ForeignKey('Ticket', on_delete=models.SET_NULL, null=True, blank=True, related_name='transaction_obj', verbose_name='بلیت')

    class Meta:
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنش ها"

    def j_create_at(self):
        if self.create_at:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''

    def __str__(self):
        return f'تراکنش شماره {self.id} | مبلغ {self.price} | ***'


# Sale Model: A proxy model for successful transactions.
class SaleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_success=True)


class Sale(Transaction):
    objects = SaleManager()

    class Meta:
        proxy = True
        verbose_name = "فروش"
        verbose_name_plural = "فروش"

    def __str__(self):
        return f'تراکنش شماره {self.id} | مبلغ {self.price} | ***'


# ProductSaleReport Model: A proxy model for product sales reports.
class ProductSaleReport(Transaction):
    objects = SaleManager()

    class Meta:
        proxy = True
        verbose_name = "گزارش فروش به تفکیک محصول"
        verbose_name_plural = "گزارش فروش به تفکیک محصول"

    def __str__(self):
        return f'{self.product}'


# ReturnedSale Model: Represents a sale return transaction.
class ReturnedSale(models.Model):
    type = models.CharField(max_length=10, choices=Transaction.TransactionType.choices, verbose_name='نوع خرید')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='return_sale', verbose_name='محصول')
    qty = models.PositiveBigIntegerField(verbose_name='تعداد')
    price = models.PositiveBigIntegerField(verbose_name='مبلغ تراکنش')
    desc = models.CharField('توضیحات', max_length=128, null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name='return_sale', verbose_name='فروشنده', null=True, blank=True)

    def j_create_at(self):
        if self.create_at:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''

    class Meta:
        verbose_name = "برگشت از فروش"
        verbose_name_plural = "برگشت از فروش"

    def __str__(self):
        return f'برگشت از فروش {self.id}'


# Ticket Model: Represents tickets related to transactions.
class Ticket(models.Model):
    tracking_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='ticket', verbose_name='محصول')
    qty = models.PositiveBigIntegerField(verbose_name='تعداد')
    transaction = models.ManyToManyField(Transaction, related_name='tickets', verbose_name='تراکنش ها')
    is_scanned = models.BooleanField('اسکن شده', default=False)
    desc = models.TextField('توضیحات', null=True, blank=True)
    is_tourist = models.BooleanField('بلیط توریستی', default=False)
    user = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.PROTECT, related_name='ticket', verbose_name='فروشنده')
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')

    class Meta:
        verbose_name = 'بلیت'
        verbose_name_plural = 'بلیت ها'

    def j_create_at(self):
        if self.create_at:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''

    # Calculate the total price of related transactions.
    def get_total_transactions(self):
        return sum([t.price for t in self.transaction.all()])

    # Calculate the total ticket price, including tax if applicable.
    def get_ticket_price(self):
        ticket_price = self.product.price * self.qty
        if self.is_tourist:
            ticket_price = self.product.tourist_price * self.qty

        tax_rate = TaxRate.objects.all().first().rate
        if self.product.is_taxable:
            ticket_price += int(ticket_price * tax_rate / 100)
        return custom_round_calculate(ticket_price)

    def __str__(self):
        return f'{self.product.title} | {self.qty} | id:{self.id}'

    # Custom validation for ticket price.
    def clean(self):
        if self.id is None:
            return
        ticket_price = self.get_ticket_price()
        total_transactions = self.get_total_transactions()

        if total_transactions < ticket_price:
            raise ValidationError(f'مبلغ بلیت از تراکنش های انجام شده {ticket_price - total_transactions} ریال بیشتر است.')

    # URL to print the ticket QR code.
    def get_ticket_url(self):
        return f'/tickets/{self.id}/print_qr/'


class Costumer(models.Model):
    first_name = models.CharField(max_length=255, verbose_name='نام', null=True, blank=True)
    last_name = models.CharField(max_length=255, verbose_name='نام خانوادگی', null=True, blank=True)
    phone = models.CharField(max_length=11, verbose_name='شماره تلفن')
    date_of_birth = jmodels.jDateField(verbose_name="تاریخ تولد", null=True, blank=True) 
    first_purchase = models.DateTimeField(auto_now_add=True, verbose_name='اولین خرید')
    last_purchase = models.DateTimeField(auto_now=True, verbose_name='آخرین خرید')

    class Meta:
        verbose_name = "مشتری"
        verbose_name_plural = "مشتریان"

    def __str__(self):
        return f'{self.name} | {self.phone}'
    

class Offer (models.Model):
    title = models.CharField(max_length=255, verbose_name='عنوان')
    description = models.TextField(verbose_name='توضیحات', null=True, blank=True)
    persent = models.PositiveIntegerField(verbose_name='درصد تخفیف')
    code = models.CharField(max_length=50, verbose_name='کد تخفیف')
    activate = models.BooleanField(default=True, verbose_name='فعال')
    set_up_time = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = "تخفیف"
        verbose_name_plural = "تخفیف ها"
        
    def __str__(self):
        return f"{self.title} | {self.persent}%"
                        
class SMS (models.Model):
    title = models.CharField(max_length=255, verbose_name='عنوان')
    description = models.TextField(verbose_name='توضیحات', help_text="این متن در پیامک برای مشتری ارسال می شود")    
    target = models.CharField(max_length=55, verbose_name="جامعه هدف", null=True, blank=True)
    activate = models.BooleanField(default=True, verbose_name='فعال')
    set_up_time = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = "پنل پیامکی"
        verbose_name_plural = "پنل پیامکی"    
        
    def __str__(self):
        return f"{self.title} | {self.target}" 
    
    
class Refund(models.Model):
    class TransactionTypeChoise(models.TextChoices):
        cash = 'cash', 'نقدی'
        card = 'card', 'کارتی'
        both = 'both', 'پوز'
    
    refund_id = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name='refund', verbose_name='تراکنش')
    ticket_tracking_code = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name='refund', verbose_name='کد رهگیری بلیت')
    refund_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ عودت وجه')
    customer_name = models.CharField(max_length=255, verbose_name='نام مشتری')
    refund_price = models.PositiveBigIntegerField(verbose_name='مبلغ برگشتی')
    transaction_type = models.CharField(max_length=255, choices=TransactionTypeChoise, verbose_name='نوع تراکش')

    class Meta:
        verbose_name = "عودت وجه"
        verbose_name_plural = "عودت وجه ها"

    def __str__(self):
        return f"Refund {self.id} - {self.customer_name}"

    def save(self, *args, **kwargs):
        if not self.refund_price:
            self.refund_price = sum(item.product.price * item.quantity for item in self.refund_products.all())
        super().save(*args, **kwargs)

class RefundProduct(models.Model):
    refund = models.ForeignKey(Refund, on_delete=models.CASCADE, related_name='refund_products', verbose_name='عودت وجه')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='refund_products', verbose_name='محصول')
    quantity = models.PositiveIntegerField(verbose_name='تعداد')

    class Meta:
        verbose_name_plural = "محصولات عودت وجه داده شده"

    def __str__(self):
        return f"{self.product.title} - {self.quantity}"
      
        
        
        
class Notification(models.Model):
    class NotificationTimeChoise(models.TextChoices):
        day = '24 ساعت', '24 ساعت'
        two_days = '48 ساعت', '48 ساعت'
        week = 'یک هفته', 'یک هفته'
        month = 'یک ماه', 'یک ماه'
    
    title = models.CharField(max_length=255, verbose_name='عنوان')
    description = models.TextField(verbose_name='توضیحات')
    activate_time = models.CharField(max_length=255, choices=NotificationTimeChoise.choices, verbose_name='اعتبار')
    activate = models.BooleanField(default=True, verbose_name='فعال')
    set_up_time = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان ها"
        
    def __str__(self):
        return f"{self.title}"

    def save(self, *args, **kwargs):
        # Determine the expiration time based on the selected activate_time
        if self.activate_time == '24 ساعت':
            expiration_time = timedelta(hours=24)
        elif self.activate_time == '48 ساعت':
            expiration_time = timedelta(hours=48)
        elif self.activate_time == 'یک هفته':
            expiration_time = timedelta(weeks=1)
        elif self.activate_time == 'یک ماه':
            expiration_time = timedelta(days=30)
        else:
            expiration_time = timedelta(0)

        # If the current time exceeds the expiration time, set activate to False
        if timezone.now() > self.set_up_time + expiration_time:
            self.activate = False

        super().save(*args, **kwargs)