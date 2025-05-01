from django.db import models
from django.contrib.auth import get_user_model
from django.core.cache import cache
import jdatetime
import uuid
from django.core.exceptions import ValidationError
from .managers import CategoryQuerySet, ProductModelManager
from treebeard.mp_tree import MP_Node
from django_jalali.db import models as jmodels
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
    gender = models.CharField(max_length=255, verbose_name='جنسیت', null=True, blank=True)
    contry = models.CharField(max_length=255, verbose_name='کشور', null=True, blank=True)
    city = models.CharField(max_length=255, verbose_name='استان', null=True, blank=True)
    phone = models.CharField(max_length=11, verbose_name='شماره تلفن', unique=True)
    date_of_birth = jmodels.jDateField(verbose_name="تاریخ تولد", null=True, blank=True) 
    first_purchase = models.DateTimeField(auto_now_add=True, verbose_name='اولین خرید')
    last_purchase = models.DateTimeField(auto_now=True, verbose_name='آخرین خرید')

    class Meta:
        verbose_name = "مشتری"
        verbose_name_plural = "مشتریان"

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
    @property
    def j_first_purchase(self):
        if self.first_purchase:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.first_purchase.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''
    
    @property
    def j_last_purchase(self):
        if self.last_purchase:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.last_purchase.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''


# Product Model: Represents a product in the system
class Product(models.Model):
    class ProductType(models.TextChoices):
        normal = ('normal', 'عادی')
        tourist = ('tourist', 'توریستی')
        
    product_type = models.CharField(max_length=10, choices=ProductType.choices, verbose_name='نوع محصول', default=ProductType.normal)
    title = models.CharField(max_length=512, verbose_name='نام محصول به فارسی', null=True, blank=True)
    title_ar = models.CharField(max_length=512, verbose_name='نام محصول به عربی', null=True, blank=True)
    title_en = models.CharField(max_length=512, verbose_name='نام محصول به انگلیسی', null=True, blank=True)
    price = models.PositiveBigIntegerField(verbose_name='قیمت')
    image = models.ImageField(upload_to='product_image/', verbose_name='تصویر', help_text='لطفا سایز عکس ۱*۱ باشد تا دیزاین سایت زیباتر باشد')    
    is_active = models.BooleanField(default=True, verbose_name='وضعیت فعال')
    is_taxable = models.BooleanField(editable=False, default=True, verbose_name='مشمول مالیات بر ارزش افزوده')
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
    
    def save(self, *args, **kwargs):
        # Check if the instance already exists and if the image is being updated
        if self.pk:  
            old_instance = Product.objects.get(pk=self.pk)
            if old_instance.image != self.image:
                # If the image is different, delete the old one
                if old_instance.image:
                    old_instance.image.delete(save=False)
        super(Product, self).save(*args, **kwargs)    


# TaxRate Model: Stores VAT tax rates.
class TaxRate(models.Model):
    rate = models.DecimalField(max_digits=4, decimal_places=2, default=10)

    class Meta:
        verbose_name = "مالیات"
        verbose_name_plural = "مالیات"

    def __str__(self):
        return str(self.rate)

    # Cache the tax rate.
    def set_cache(self):
        cache.set(self.__class__.__name__, self)

    def save(self, *args, **kwargs):
        # Ensures only one instance of this model exists by setting pk to 1.
        if not self.pk:  # If the object doesn't exist yet, it will be created
            self.pk = 1
        super().save(*args, **kwargs)
        self.set_cache()

    def delete(self, *args, **kwargs):
        # Prevent deletion of the tax rate.
        raise Exception("TaxRate cannot be deleted.")

    # Load tax rate from cache, or fetch from database.
    @classmethod
    def load(cls):
        # Attempt to load the tax rate from the cache
        tax_rate = cache.get(cls.__name__)
        if tax_rate is None:
            tax_rate, created = cls.objects.get_or_create(pk=1)
            if not created:
                tax_rate.set_cache()
        return tax_rate
    
    
    
class Offer (models.Model): 
    title = models.CharField(max_length=255, verbose_name='عنوان')
    description = models.TextField(verbose_name='توضیحات', null=True, blank=True)
    persent = models.PositiveIntegerField(verbose_name='درصد تخفیف')
    code = models.CharField(max_length=50, verbose_name='کد تخفیف', help_text="نکته مهم : تمام حروف ها باید انگلیسی و کوچک باشد")
    activate = models.BooleanField(default=True, verbose_name='فعال')
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = "تخفیف"
        verbose_name_plural = "تخفیف ها"
        
    def __str__(self):
        return f"{self.code}"
    
    def j_create_at(self):
        if self.create_at:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''    
        


# Transaction Model: Stores transaction details.
class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        pc = ('pc', 'دستگاه کارتخوان')
        cash = ('cash', 'نقدی')
        mix = ('mix', 'ترکیبی')

    id = models.AutoField(primary_key=True, verbose_name="کد رهگیری فروش")
    tracking_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name='فروشنده')
    ticket = models.ForeignKey('Ticket', on_delete=models.PROTECT, related_name='transaction_obj', verbose_name='بلیت')
    type = models.CharField(max_length=10, choices=TransactionType.choices, verbose_name='نوع تراکنش', default=TransactionType.pc)
    mix_pc = models.PositiveBigIntegerField(verbose_name='مقدار قیمت پرداخت شده با دستگاه کارتخوان',  null=True, blank=True, help_text="در صورتی که نوع فروش ترکیبی باشد این فیلد به صورت اتوماتیک دریافت میشود")
    mix_cash = models.PositiveBigIntegerField(verbose_name='مقدار قیمت پرداخت شده نقدی',  null=True, blank=True, help_text="در صورتی که نوع فروش ترکیبی باشد این فیلد به صورت اتوماتیک دریافت میشود")
    is_success = models.BooleanField('تراکنش موفق', default=True, help_text='این فروش را نیازی نیست حذف کنید فقط تیک این فیلد را بردارید')
    has_tax = models.BooleanField('با احتساب مالیات بر ارزش افزورده', default=True)
    offer = models.ForeignKey('Offer', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', verbose_name='کد تخفیف')
    manual_discount = models.PositiveIntegerField(verbose_name='تخفیف دستی', default=0, null=True, blank=True)
    product_prices = models.PositiveBigIntegerField(verbose_name='مجموع مبلغ محصولات')
    tax = models.PositiveBigIntegerField(verbose_name='مبلغ مالیات', null=True, blank=True)
    discount = models.PositiveBigIntegerField(verbose_name='مبلغ تخفیف',  null=True, blank=True)
    price = models.PositiveBigIntegerField(verbose_name='قیمت نهایی',  null=True, blank=True,)
    desc = models.TextField('توضیحات', null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت تراکنش')

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
    
    def calculate_product_prices(self):
        total_price = 0
        # Iterate over the related ticket_products to sum the price
        for ticket in self.ticket.ticket_products.all():
            total_price += ticket.product.price * ticket.quantity
        return total_price
    
    def clean(self):
        # Validate manual_discount
        if self.manual_discount and self.manual_discount < 0:
            raise ValidationError("تخفیف دستی نمی‌تواند منفی باشد.")
        
        # Validate offer percentage
        if self.offer and (self.offer.persent < 0 or self.offer.persent > 100):
            raise ValidationError("درصد تخفیف باید بین 0 تا 100 باشد.")
        
        # If an offer is applied, manual_discount should be 0
        if self.offer and self.offer.activate and self.manual_discount:
            raise ValidationError("هنگام استفاده از کد تخفیف، تخفیف دستی نباید وارد شود.")

    def save(self, *args, **kwargs):
        # Run custom validation before saving the transaction
        self.clean()
        
        # Initialize fields if they are None
        self.product_prices = self.product_prices or 0
        self.discount = self.discount or 0
        self.tax = self.tax or 0
        self.manual_discount = self.manual_discount or 0

        # Calculate and update the product_prices field before saving
        if self.ticket:
            self.product_prices = self.calculate_product_prices()

        # Apply tax if 'has_tax' is True
        if self.has_tax:
            tax_rate = TaxRate.objects.first().rate  # Assuming there is only one tax rate
            self.tax = int(self.product_prices * tax_rate / 100)
        else:
            self.tax = 0  # Ensure tax is zero when has_tax is False

        # Calculate total amount before discount
        total_amount = self.product_prices + self.tax

        # Apply discount calculation
        if self.offer and self.offer.activate:
            offer_discount = total_amount * self.offer.persent / 100
            # If an offer is applied, set manual_discount to 0
            self.manual_discount = 0
        else:
            offer_discount = 0

        # Calculate the total discount: Offer discount + manual discount
        self.discount = offer_discount + self.manual_discount

        # Validate discount
        if self.discount > total_amount:
            raise ValidationError("مجموع تخفیف نمی‌تواند بیشتر از مجموع قیمت محصولات و مالیات باشد.")

        # Calculate final price (product price + tax - discount)
        self.price = total_amount - self.discount

        super().save(*args, **kwargs)




# Ticket Model: Represents tickets related to transactions.
class Ticket(models.Model):
    tracking_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    transaction = models.ManyToManyField(Transaction, related_name='tickets', verbose_name='تراکنش ها')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='ticket', verbose_name='مشتری', null=True, blank=True)
    desc = models.TextField('توضیحات', null=True, blank=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name='ticket', verbose_name='فروشنده')
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

    # URL to print the ticket QR code.
    def get_ticket_url(self):
        return f'/tickets/{self.id}/print_qr/'

    def __str__(self):
        return f'کد رهگیری بلیت: {self.id}'        
    
    def total_price(self):
        return sum(item.product.price * item.quantity for item in self.ticket_products.all())

    def calculate_tax(self):
        tax_rate = TaxRate.objects.first().rate 
        return int(self.total_price() * tax_rate / 100)

    def calculate_final_price(self):
        return self.total_price() + self.calculate_tax()    
    


class TicketProduct(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='ticket_products', verbose_name='بلیت')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='ticket_products', verbose_name='محصول')
    quantity = models.PositiveIntegerField(verbose_name='تعداد', default=1)
    scanned = models.BooleanField(verbose_name="اسکن شده", default=False)

    class Meta:
        verbose_name_plural = "محصولات بلیت"

    def __str__(self):
        return f"کد رهگیری بلیت : {self.ticket.id} | محصولات : {self.product.title} (*) تعداد : {self.quantity} (*) قیمت : {self.product.price} ریال"
    
    def get_total_price(self):
        return self.product.price * self.quantity    
    
    
@receiver(post_save, sender=TicketProduct)
@receiver(post_delete, sender=TicketProduct)
def update_transaction_product_prices(sender, instance, **kwargs):
    for transaction in instance.ticket.transaction.all():
        total_price = sum(tp.product.price * tp.quantity for tp in instance.ticket.ticket_products.all())
        transaction.product_prices = total_price
        transaction.save()
    
    
    
    
# ReturnedTransaction Model: Represents a transaction return transaction.
class ReturnedTransaction(models.Model):
    class FoundType(models.TextChoices):
        cash = ('نقد', 'نقد')
        send_money_by_card_number = ('کارت به کارت', 'کارت به کارت')
        send_money_by_sheba_number = ('انتقال با شماره شبا', 'انتقال با شماره شبا')    
    
    id = models.AutoField(primary_key=True, verbose_name="کد رهگیری عودت وجه")
    tracking_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    transaction = models.ForeignKey('Transaction', on_delete=models.PROTECT, related_name='return_transaction', verbose_name='کد رهگیری فروش')
    type = models.CharField(max_length=55, choices=FoundType.choices, verbose_name='نوع عودت وجه', default=FoundType.cash)
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, verbose_name='فروشنده')
    desc = models.TextField('توضیحات', null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')
    source_card_holder_name = models.CharField(verbose_name='نام صاحب کارت مبدا', max_length=128, null=True, blank=True, help_text="درصورتی که نوع عودت وجه را از طریق شماره کارت یا شماره شبا انتخاب کرده اید این فیلد را پر کنید") 
    destination_card_holder_name = models.CharField(verbose_name='نام صاحب کارت مقصد', max_length=128, null=True, blank=True, help_text="درصورتی که نوع عودت وجه را از طریق شماره کارت یا شماره شبا انتخاب کرده اید این فیلد را پر کنید")
    source_card_number = models.CharField(verbose_name='شماره کارت مبدا', max_length=16, null=True, blank=True, help_text="درصورتی که نوع عودت وجه را از طریق شماره کارت یا شماره شبا انتخاب کرده اید این فیلد را پر کنید") 
    destination_card_number = models.CharField(verbose_name='شماره کارت مقصد', max_length=16, null=True, blank=True, help_text="درصورتی که نوع عودت وجه را از طریق شماره کارت یا شماره شبا انتخاب کرده اید این فیلد را پر کنید") 
    source_sheba_number = models.CharField(verbose_name='شماره شبا مبدا', max_length=24, null=True, blank=True, help_text="درصورتی که نوع عودت وجه را از طریق شماره کارت یا شماره شبا انتخاب کرده اید این فیلد را پر کنید") 
    destination_sheba_number = models.CharField(verbose_name='شماره شبا مقصد', max_length=24, null=True, blank=True, help_text="درصورتی که نوع عودت وجه را از طریق شماره کارت یا شماره شبا انتخاب کرده اید این فیلد را پر کنید") 

    class Meta:
        verbose_name = "عودت وجه"
        verbose_name_plural = "عودت وجه"

    def j_create_at(self):
        if self.create_at:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''

    def __str__(self):
        return f'{self.id}'      
   
    def save(self, *args, **kwargs):
        # Ensure the Transaction exists and is valid for a refund
        if not self.transaction.is_success:
            raise ValidationError("این تراکنش ناموفق بوده یا قبلا عودت وجه داده شده")

        # Check if this Transaction has already been refunded
        if ReturnedTransaction.objects.filter(transaction=self.transaction).exists():
            raise ValidationError("این تراکنش ناموفق بوده یا قبلا عودت وجه داده شده")

        # Perform the refund logic
        self.transaction.is_success = False
        self.transaction.save()

        super().save(*args, **kwargs)

    def clean(self):
        if not self.transaction.is_success:
            raise ValidationError("این تراکنش ناموفق بوده یا قبلا عودت وجه داده شده")
        return super().clean()
    

                        
class SMS(models.Model):
    # انتخاب‌های مربوط به دسته‌بندی‌ها
    TARGET_CHOICES = (
        ('کل مشتری ها', 'کل مشتری ها'),
        ('تولد ها', 'تولد ها'),
        ('مشتری های توریست', 'مشتری های توریست'),
        ('دهه هشتادی ها', 'دهه هشتادی ها'),
        ('دهه هفتادی ها', 'دهه هفتادی ها'),
        ('شماره های 0912', 'شماره های 0912'),
        ('تاپ تن مشتری های پرخرید', 'تاپ تن مشتری های پرخرید'),
        ('۱۰۰ مشتری پرخرید اول', '۱۰۰ مشتری پرخرید اول'),
        ('خرید اول', 'خرید اول'),
        ('خرید دهم', 'خرید دهم'),
        ('خرید صدم', 'خرید صدم'),
        ('سال نو', 'سال نو'),
        ('یلدا', 'یلدا'),
        ('تولد ها (پیام به آنهایی که تولدشان امروزه)', 'تولد ها (پیام به آنهایی که تولدشان امروزه)'),
        ('سیزده بدر', 'سیزده بدر'),
        ('آغاز تابستان', 'آغاز تابستان'),
        ('آغاز پاییز', 'آغاز پاییز'),
        ('آغاز زمستان', 'آغاز زمستان'),
    )

    title = models.CharField(max_length=255, verbose_name='عنوان')
    description = models.TextField(verbose_name='توضیحات', help_text="این متن در پیامک برای مشتری ارسال می شود")
    target = models.CharField(max_length=55, choices=TARGET_CHOICES, verbose_name="جامعه هدف", null=True, blank=True)
    activate = models.BooleanField(default=True, verbose_name='فعال')
    j_create_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = "پنل پیامکی"
        verbose_name_plural = "پنل پیامکی"
        
    def __str__(self):
        return f"{self.title} | {self.target}" 
    
    
        
class Notification(models.Model):
    title = models.CharField(max_length=255, verbose_name='عنوان')
    description = models.TextField(verbose_name='توضیحات')
    activate = models.BooleanField(default=True, verbose_name='فعال')
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')  # Fixed field name
    
    class Meta:
        verbose_name = "نوتیفیکیشن"
        verbose_name_plural = "نوتیفیکیشن ها"
        
    def __str__(self):
        return f"{self.title}"

    def j_create_at(self):
        if self.create_at:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at)  # Convert to Jalali
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''     
    

class RerecordingTransaction(models.Model):
    class TransactionType(models.TextChoices):
        pc = ('pc', 'pc pos')
        cash = ('cash', 'نقدی')
        card = ('card', 'کارتی')

    id = models.AutoField(primary_key=True, verbose_name="کد رهگیری فروش مجدد")
    rerecording_transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name='rerecording', verbose_name='کد رهگیری تراکنش') 
    type = models.CharField(max_length=10, choices=Transaction.TransactionType.choices, verbose_name='نوع تراکنش', default=Transaction.TransactionType.pc)    
    mix_pc = models.PositiveBigIntegerField(verbose_name='مقدار قیمت پرداخت شده با دستگاه کارتخوان',  null=True, blank=True, help_text="در صورتی که نوع فروش ترکیبی باشد این فیلد به صورت اتوماتیک دریافت میشود")
    mix_cash = models.PositiveBigIntegerField(verbose_name='مقدار قیمت پرداخت شده نقدی',  null=True, blank=True, help_text="در صورتی که نوع فروش ترکیبی باشد این فیلد به صورت اتوماتیک دریافت میشود")
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name='rerecording_transactions', verbose_name='فروشنده', null=True, blank=True)  
    is_success = models.BooleanField('تراکنش موفق', default=True, help_text='این فیلد را نیازی نیست حذف کنید فقط تیک این فیلد را بردارید')
    desc = models.TextField('توضیحات', null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')

    class Meta:
        verbose_name = "تراکنش مجدد"
        verbose_name_plural = "تراکنش های مجدد"

    def clean(self):
        if self.rerecording_transaction and not self.rerecording_transaction.is_success:
            raise ValidationError("سیستم قادر به ثبت فروش مجدد برای تراکنش ناموفق نیست")

    def save(self, *args, **kwargs):
        # Ensure the parent transaction is successful
        if self.rerecording_transaction and not self.rerecording_transaction.is_success:
            raise ValidationError("سیستم قادر به ثبت فروش مجدد برای تراکنش ناموفق نیست")

        # Update parent transaction status if needed
        if self.rerecording_transaction and (self.is_success != self.rerecording_transaction.is_success):
            self.rerecording_transaction.is_success = self.is_success
            self.rerecording_transaction.save()

        # Only perform cloning on first save (i.e. creation)
        if not self.pk:
            old_transaction = self.rerecording_transaction
            old_ticket = old_transaction.ticket

            # Step 1: Create a new ticket (the new ticket gets its own tracking_code automatically)
            new_ticket = Ticket.objects.create(
                customer=old_ticket.customer,
                desc=self.desc or old_ticket.desc,
                user=self.user or old_ticket.user,
            )

            # Step 2: Copy all TicketProduct records from the old ticket to the new ticket.
            for ticket_product in old_ticket.ticket_products.all():
                TicketProduct.objects.create(
                    ticket=new_ticket,
                    product=ticket_product.product,
                    quantity=ticket_product.quantity,
                    scanned=False,
                )

            # Step 3: Create a new transaction using the new ticket
            new_transaction = Transaction(
                user=self.user or old_transaction.user,
                ticket=new_ticket,  # New ticket now contains TicketProduct records!
                type=self.type,
                is_success=self.is_success,
                has_tax=old_transaction.has_tax,
                offer=old_transaction.offer,
                manual_discount=old_transaction.manual_discount,
                mix_pc=self.mix_pc,
                mix_cash=self.mix_cash,
                desc=self.desc or old_transaction.desc,
                # Do not pass product_prices, tax, discount, or price;
                # these will be recalculated in Transaction.save()
            )
            new_transaction.save()

            # Link the new transaction to the new ticket (ManyToMany relationship)
            new_ticket.transaction.add(new_transaction)

            # Update the rerecording_transaction field to point to the new transaction
            self.rerecording_transaction = new_transaction

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.id}"

    def j_create_at(self):
        if self.create_at:
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at.astimezone())
            return jalali_date.strftime('%Y/%m/%d %H:%M')
        return ''
    
    
    
class SaleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_success=True)    
    
    
class ProductSaleReport(Transaction):

    objects = SaleManager()

    class Meta:
        proxy = True
        verbose_name = "گزارش فروش به تفکیک محصول"          
        verbose_name_plural = "گزارش فروش به تفکیک محصول"     

    def __str__(self) -> str:
        return f'{self.product}'    
    
    
    
class SellerSaleReport(Transaction):
    class Meta:
        proxy = True
        verbose_name = "گزارش فروش به تفکیک صندوق داران"
        verbose_name_plural = "گزارش فروش به تفکیک صندوق داران"


class CustomerPurchaseReport(Transaction):
    class Meta:
        proxy = True
        verbose_name = "گزارش فروش به تفکیک مشتریان"
        verbose_name_plural = "گزارش فروش به تفکیک مشتریان"
    