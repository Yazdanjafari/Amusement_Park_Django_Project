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
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

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


class Customer(models.Model):
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
        return f'{self.first_name} {self.last_name}'


# Product Model: Represents a product in the system.
class Product(models.Model):
    title = models.CharField(max_length=512, verbose_name='نام محصول', unique=True)
    price = models.PositiveBigIntegerField(verbose_name='قیمت')
    tourist_price = models.PositiveBigIntegerField(default=0, verbose_name='قیمت توریستی')
    image = models.ImageField(upload_to='product_image/', verbose_name='تصویر', help_text='لطفا سایز عکس ۱*۱ باشد تا دیزاین سایت زیباتر باشد')
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
        return f"{self.code}"
    
        


# Transaction Model: Stores transaction details.
class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        pc = ('pc', 'pc pos')
        cash = ('cash', 'نقدی')
        card = ('card', 'کارتی')

    id = models.AutoField(primary_key=True, verbose_name="کد رهگیری فروش")
    tracking_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name='transactions', verbose_name='فروشنده')
    ticket = models.ForeignKey('Ticket', on_delete=models.SET_NULL, null=True, blank=True, related_name='transaction_obj', verbose_name='بلیت')
    type = models.CharField(max_length=10, choices=TransactionType.choices, verbose_name='نوع تراکنش', default=TransactionType.pc)
    is_success = models.BooleanField('تراکنش موفق', default=True)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت تراکنش')
    offer = models.ForeignKey('Offer', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', verbose_name='کد تخفیف')
    has_tax = models.BooleanField('با احتساب مالیات بر ارزش افزورده', default=True)
    product_prices = models.PositiveBigIntegerField(verbose_name='مجموع مبلغ محصولات')
    tax = models.PositiveBigIntegerField(verbose_name='مبلغ مالیات', null=True, blank=True)
    discount = models.PositiveBigIntegerField(verbose_name='مبلغ تخفیف', default=0, null=True, blank=True)
    price = models.PositiveBigIntegerField(verbose_name='قیمت نهایی')
    desc = models.TextField('توضیحات', null=True, blank=True)

    class Meta:
        verbose_name = "فروش"
        verbose_name_plural = "فروش ها"

    def j_create_at(self):
        if self.create_at:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''

    def __str__(self):
        return f'{self.id}'


# Sale Model: A proxy model for successful transactions.
class SaleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_success=True)


class Sale(Transaction):
    objects = SaleManager()

    class Meta:
        proxy = True
        verbose_name = "فروش های موفق"
        verbose_name_plural = "فروش های موفق"

    def __str__(self):
        return f'{self.id}'



# Ticket Model: Represents tickets related to transactions.
class Ticket(models.Model):
    tracking_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    transaction = models.ManyToManyField(Transaction, related_name='tickets', verbose_name='تراکنش ها')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='ticket', verbose_name='مشتری', null=True, blank=True)
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
        ticket_price = sum(tp.product.price * tp.quantity for tp in self.ticket_products.all())
        if self.is_tourist:
            ticket_price = sum(tp.product.tourist_price * tp.quantity for tp in self.ticket_products.all())

        tax_rate = TaxRate.objects.all().first().rate
        if any(tp.product.is_taxable for tp in self.ticket_products.all()):
            ticket_price += int(ticket_price * tax_rate / 100)
        return custom_round_calculate(ticket_price)



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

    def __str__(self):
        return f'مشتری : {self.customer} | کد رهگیری بلیت: {self.id}'        


class TicketProduct(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='ticket_products', verbose_name='بلیت')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='ticket_products', verbose_name='محصول')
    quantity = models.PositiveIntegerField(verbose_name='تعداد', default=1)

    class Meta:
        verbose_name_plural = "محصولات بلیت"

    def __str__(self):
        return f"کد رهگیری بلیت : {self.ticket.id} | نام مشتری : {self.ticket.customer.first_name} {self.ticket.customer.last_name} | محصولات : {self.product.title} (*) تعداد : {self.quantity} (*) قیمت : {self.product.price} ریال"
    
    
# ReturnedSale Model: Represents a sale return transaction.
class ReturnedSale(models.Model):
    class FoundType(models.TextChoices):
        cash = ('نقد', 'نقد')
        send_money_by_card_number = ('کارت به کارت', 'کارت به کارت')
        send_money_by_sheba_number = ('انتقال با شماره شبا', 'انتقال با شماره شبا')    
    
    id = models.AutoField(primary_key=True, verbose_name="کد رهگیری عودت وجه")
    sale = models.ForeignKey('Sale', on_delete=models.PROTECT, related_name='return_sale', verbose_name='کد رهگیری فروش')
    type = models.CharField(max_length=55, choices=FoundType.choices, verbose_name='نوع عودت وجه', default=FoundType.cash)
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name='returned_sales', verbose_name='فروشنده', null=True, blank=True)
    is_success = models.BooleanField('تراکنش موفق', default=True)
    desc = models.CharField('توضیحات', max_length=128, null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')
    source_card_holder_name = models.CharField(verbose_name='نام صاحب کارت مبدا', max_length=128, null=True, blank=True, help_text="درصورتی که نوع عودت وجه را از طریق شماره کارت یا شماره شبا انتخاب کرده اید این فیلد را پر کنید") 
    destination_card_holder_name = models.CharField(verbose_name='نام صاحب کارت مقصد', max_length=128, null=True, blank=True, help_text="درصورتی که نوع عودت وجه را از طریق شماره کارت یا شماره شبا انتخاب کرده اید این فیلد را پر کنید")
    source_card_number = models.CharField(verbose_name='شماره کارت مبدا', max_length=16, null=True, blank=True, help_text="درصورتی که نوع عودت وجه را از طریق شماره کارت یا شماره شبا انتخاب کرده اید این فیلد را پر کنید") 
    destination_card_number = models.CharField(verbose_name='شماره کارت مقصد', max_length=16, null=True, blank=True, help_text="درصورتی که نوع عودت وجه را از طریق شماره کارت یا شماره شبا انتخاب کرده اید این فیلد را پر کنید") 
    source_sheba_number = models.CharField(verbose_name='شماره شبا مبدا', max_length=24, null=True, blank=True, help_text="درصورتی که نوع عودت وجه را از طریق شماره کارت یا شماره شبا انتخاب کرده اید این فیلد را پر کنید") 
    destination_sheba_number = models.CharField(verbose_name='شماره شبا مقصد', max_length=24, null=True, blank=True, help_text="درصورتی که نوع عودت وجه را از طریق شماره کارت یا شماره شبا انتخاب کرده اید این فیلد را پر کنید") 



    def j_create_at(self):
        if self.create_at:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''

    class Meta:
        verbose_name = "عودت وجه"
        verbose_name_plural = "عودت وجه"

    def __str__(self):
        return f'{self.id}'    
   
                        
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

    def j_create_at(self):
        if self.create_at:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''      
      
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

        # Check if set_up_time is not None before performing the comparison
        if self.set_up_time and timezone.now() > self.set_up_time + expiration_time:
            self.activate = False

        super().save(*args, **kwargs)
        
        
        
        
class RerecordingTransaction(models.Model):
    class TransactionType(models.TextChoices):
        pc = ('pc', 'pc pos')
        cash = ('cash', 'نقدی')
        card = ('card', 'کارتی')

    id = models.AutoField(primary_key=True, verbose_name="کد رهگیری فروش مجدد")
    rerecording_transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name='rerecording', verbose_name='کد رهگیری تراکنش مادر') 
    type = models.CharField(max_length=10, choices=TransactionType.choices, verbose_name='نوع تراکنش', default=TransactionType.pc)    
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name='rerecording_transactions', verbose_name='فروشنده', null=True, blank=True)  
    is_success = models.BooleanField('تراکنش موفق', default=True)
    desc = models.TextField('توضیحات', null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')
    
    class Meta:
        verbose_name = "فروش مجدد"
        verbose_name_plural = "فروش های مجدد"
        
    def __str__(self):
        return f"{self.id}"  
    
    def j_create_at(self):
        if self.create_at:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''    
    

class SuccessfulTransactionLog(models.Model):
    class TransactionKind(models.TextChoices):
        TRANSACTION = 'فروش', 'فروش'
        RERECORDING = 'فروش مجدد', 'فروش مجدد'
        RETURNED_SALE = 'عودت وجه', 'عودت وجه'

    id = models.AutoField(primary_key=True, verbose_name="کد رهگیری تراکنش")
    kind = models.CharField(max_length=30, choices=TransactionKind.choices, verbose_name="نوع تراکنش")
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name='successful_sales', verbose_name='فروشنده', null=True, blank=True)
    desc = models.TextField('توضیحات', null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')
    
    sale = models.ForeignKey('Sale', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='کد رهگیری فروش')
    rerecording = models.ForeignKey('RerecordingTransaction', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='کد رهگیری فروش مجدد')
    returned_sale = models.ForeignKey('ReturnedSale', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='کد رهگیری عودت وجه')    
    

    class Meta:
        verbose_name = "تراکنش ها"
        verbose_name_plural = "تراکنش ها"

    def __str__(self):
        return f"کد رهگیری تراکنش: {self.id} | نوع تراکنش: {self.kind}"
    
    def j_create_at(self):
        if self.create_at:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''          
    

# Signal handlers to create, update, and delete SuccessfulTransactionLog entries
@receiver(post_save, sender=Transaction)
def create_or_update_successful_transaction_log(sender, instance, created, **kwargs):
    if instance.is_success:
        log, created = SuccessfulTransactionLog.objects.update_or_create(
            sale=instance,
            defaults={
                'kind': SuccessfulTransactionLog.TransactionKind.TRANSACTION,
                'user': instance.user,
                'desc': instance.desc,
                'create_at': instance.create_at,
            }
        )

@receiver(post_delete, sender=Transaction)
def delete_successful_transaction_log(sender, instance, **kwargs):
    SuccessfulTransactionLog.objects.filter(sale=instance).delete()

@receiver(post_save, sender=RerecordingTransaction)
def create_or_update_successful_rerecording_log(sender, instance, created, **kwargs):
    if instance.is_success:
        log, created = SuccessfulTransactionLog.objects.update_or_create(
            rerecording=instance,
            defaults={
                'kind': SuccessfulTransactionLog.TransactionKind.RERECORDING,
                'user': instance.user,
                'desc': instance.desc,
                'create_at': instance.create_at,
            }
        )

@receiver(post_delete, sender=RerecordingTransaction)
def delete_successful_rerecording_log(sender, instance, **kwargs):
    SuccessfulTransactionLog.objects.filter(rerecording=instance).delete()

@receiver(post_save, sender=ReturnedSale)
def create_or_update_successful_returned_sale_log(sender, instance, created, **kwargs):
    if instance.is_success:
        log, created = SuccessfulTransactionLog.objects.update_or_create(
            returned_sale=instance,
            defaults={
                'kind': SuccessfulTransactionLog.TransactionKind.RETURNED_SALE,
                'user': instance.user,
                'desc': instance.desc,
                'create_at': instance.create_at,
            }
        )

@receiver(post_delete, sender=ReturnedSale)
def delete_successful_returned_sale_log(sender, instance, **kwargs):
    SuccessfulTransactionLog.objects.filter(returned_sale=instance).delete()