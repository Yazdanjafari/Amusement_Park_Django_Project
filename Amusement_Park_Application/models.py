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
from .managers import CategoryQuerySet,ProductModelManager
from treebeard.mp_tree import MP_Node


class Category(MP_Node):
    title = models.CharField(max_length=255, db_index=True,verbose_name='عنوان')
    is_active = models.BooleanField(default=True,verbose_name='فعال')
    products = models.ManyToManyField('Product', related_name='categories')


    node_order_by = ['title']
    objects = CategoryQuerySet.as_manager()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "دسته بندی"
        verbose_name_plural = "دسته بندی"

    def get_products(self):
        return "\n,".join([p.title for p in self.products.all()])


    


class Product(models.Model):
    title = models.CharField(max_length=512,verbose_name='نام محصول',unique=True)
    price = models.PositiveBigIntegerField(verbose_name='قیمت')
    tourist_price = models.PositiveBigIntegerField(default=0,verbose_name='قیمت توریستی')
    image = models.ImageField(upload_to='product_image/',verbose_name='تصویر',help_text='سایز 800*800')
    is_active = models.BooleanField(default=True,verbose_name='وضعیت فعال')
    is_taxable =  models.BooleanField(default=False,verbose_name='مشمول مالیات بر ارزش افزوده')
    order_metric = models.PositiveIntegerField(editable=False,default=0)

    created=models.DateTimeField(auto_now_add=True,verbose_name=' زمان ایجاد')
    update=models.DateTimeField(auto_now=True,verbose_name=' زمان ویرایش')

    objects = ProductModelManager()

    class Meta:
        verbose_name = "محصول"          
        verbose_name_plural = "محصولات"     
        ordering = ('-order_metric',)

    def __str__(self) -> str:
        return f'{self.title}'
    
    def j_update(self):
        if self.update :
            jalali_date = jdatetime.datetime.fromgregorian(date=self.update.astimezone())
            jalali_date_string = jalali_date.strftime('%Y/%m/%d %H:%M')
            return jalali_date_string
        else :
            return ''

    def j_created(self):
        if self.created :
            jalali_date = jdatetime.datetime.fromgregorian(date=self.created.astimezone())
            jalali_date_string = jalali_date.strftime('%Y/%m/%d %H:%M')
            return jalali_date_string
        else :
            return ''   


class TaxRate(models.Model):
    rate = models.DecimalField(max_digits=4, decimal_places=2,default=9)

    class Meta:
        verbose_name = "نرخ مالیات بر ارزش افزوده"
        verbose_name_plural = "نرخ مالیات بر ارزش افزوده"

    def __str__(self) -> str:
        return str(self.rate)
    
    def set_cache(self):
        cache.set(self.__class__.__name__, self)


    def save(self, *args, **kwargs):
        self.pk = 1
        super(TaxRate, self).save(*args, **kwargs)
        self.set_cache()


    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        if cache.get(cls.__name__) is None:
            obj, created = cls.objects.get_or_create(pk=1)
            if not created:
                obj.set_cache()
        return cache.get(cls.__name__)
    

class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        pc = ('pc','pc pos')
        cash = ('cash','نقدی')
        card = ('card','کارتی')

    tracking_code = models.UUIDField(default=uuid.uuid4, editable=False,unique=True)
    type = models.CharField(max_length=10,choices=TransactionType.choices,verbose_name='نوع تراکنش',default=TransactionType.card)
    is_success = models.BooleanField('تراکنش موفق',default=False)
    # product = models.ForeignKey(Product,on_delete=models.PROTECT,null=True,blank=True,related_name='transaction',verbose_name='محصول')
    # qty = models.PositiveBigIntegerField(verbose_name='تعداد',null=True,blank=True,)
    # is_scanned = models.BooleanField('اسکن شده',default=False)
    price = models.PositiveBigIntegerField(verbose_name='مبلغ تراکنش')
    trans_id = models.CharField(max_length=128,verbose_name='شماره تراکنش',null=True,blank=True)
    date = models.CharField(max_length=128,verbose_name='زمان تراکنش',null=True,blank=True)
    desc = models.TextField('توضیحات',null=True,blank=True)
    create_at=models.DateTimeField(auto_now_add=True,verbose_name='زمان ثبت')
    user = models.ForeignKey(get_user_model(),on_delete=models.PROTECT,related_name='sale',verbose_name='فروشنده')
    has_tax = models.BooleanField('با احتساب ارزش افزورده',default=False)
    discount = models.PositiveBigIntegerField(default = 0,null=True,blank=True, verbose_name='مبلغ تخفیف')
    ticket = models.ForeignKey('Ticket',on_delete=models.SET_NULL,null=True,blank=True,related_name='transaction_obj',verbose_name='بلیت')
    
    class Meta:
        verbose_name = "تراکنش"          
        verbose_name_plural = "تراکنش ها"     

    def j_create_at(self):
        if self.create_at :
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at.astimezone())
            jalali_date_string = jalali_date.strftime('%Y/%m/%d %H:%M')
            return jalali_date_string
        else :
            return ''  

    
    def __str__(self) -> str:
        # return f'تراکنش شماره {self.id} | مبلغ {self.price} | {self.ticket.product.title}'
        return f'تراکنش شماره {self.id} | مبلغ {self.price} | ***'





class SaleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_success=True)
    

class Sale(Transaction):

    objects = SaleManager()

    class Meta:
        proxy = True
        verbose_name = "فروش"          
        verbose_name_plural = "فروش"     

    def __str__(self) -> str:

        return f'تراکنش شماره {self.id} | مبلغ {self.price} | ***'

class ProductSaleReport(Transaction):

    objects = SaleManager()

    class Meta:
        proxy = True
        verbose_name = "گزارش فروش به تفکیک محصول"          
        verbose_name_plural = "گزارش فروش به تفکیک محصول"     

    def __str__(self) -> str:
        return f'{self.product}'
    

class ReturnedSale(models.Model):

    type = models.CharField(max_length=10,choices=Transaction.TransactionType.choices,verbose_name='نوع خرید')
    product = models.ForeignKey(Product,on_delete=models.PROTECT,related_name='return_sale',verbose_name='محصول')
    qty = models.PositiveBigIntegerField(verbose_name='تعداد')
    price = models.PositiveBigIntegerField(verbose_name='مبلغ تراکنش')
    desc = models.CharField('توضیحات',max_length=128,null=True,blank=True)
    create_at=models.DateTimeField(auto_now_add=True,verbose_name='زمان ثبت')
    user = models.ForeignKey(get_user_model(),on_delete=models.PROTECT,related_name='return_sale',verbose_name='فروشنده',null=True,blank=True)

    def j_create_at(self):
        if self.create_at :
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at.astimezone())
            jalali_date_string = jalali_date.strftime('%Y/%m/%d %H:%M')
            return jalali_date_string
        else :
            return ''  
        
    class Meta:
        verbose_name = "برگشت از فروش"          
        verbose_name_plural = "برگشت از فروش"     


    def __str__(self) -> str:
        return f'برگشت از فروش {self.id}'
    


class Ticket(models.Model):
    tracking_code = models.UUIDField(default=uuid.uuid4, editable=False,unique=True)

    product = models.ForeignKey(Product,on_delete=models.PROTECT,related_name='ticket',verbose_name='محصول')
    qty = models.PositiveBigIntegerField(verbose_name='تعداد')
    transaction = models.ManyToManyField(Transaction,related_name='tickets',verbose_name='تراکنش ها')
    is_scanned = models.BooleanField('اسکن شده',default=False)
    desc = models.TextField('توضیحات',null=True,blank=True)
    is_tourist = models.BooleanField('بلیط توریستی',default=False)
    user = models.ForeignKey(get_user_model(),null=True,blank=True,on_delete=models.PROTECT,related_name='ticket',verbose_name='فروشنده')
    create_at=models.DateTimeField(auto_now_add=True,verbose_name='زمان ثبت')   
   

    class Meta:
        verbose_name ='بلیت'       
        verbose_name_plural = 'بلیت ها'

    def j_create_at(self):
        if self.create_at :
            jalali_date = jdatetime.datetime.fromgregorian(date=self.create_at.astimezone())
            jalali_date_string = jalali_date.strftime('%Y/%m/%d %H:%M')
            return jalali_date_string
        else :
            return ''  
        
    def get_total_transactions(self):
        sum = 0
        transactions = self.transaction.all()
        for t in transactions:
            sum +=t.price
        return sum

    def get_ticket_price(self):
        ticket_price = self.product.price * self.qty
        if self.is_tourist == True:
            ticket_price = self.product.tourist_price * self.qty

        tax_rate = TaxRate.objects.all().first().rate
        if self.product.is_taxable:
            ticket_price = ticket_price + int(ticket_price * tax_rate/100)
        return custom_round_calculate(ticket_price)
    

    
    def __str__(self) -> str:
        return f'{self.product.title} | {self.qty} | id:{self.id} '
    
    def clean(self):
        if self.id == None:
            return 
        ticket_price = self.get_ticket_price()
        total_transactions = self.get_total_transactions()

        print(f'ticket_price = {ticket_price}  total_transactions={total_transactions}')
        # if abs(ticket_price - total_transactions) > 10000:
        if total_transactions < ticket_price  :
            raise ValidationError(f'مبلغ بلیت از تراکنش های انجام شده {ticket_price-total_transactions} ریال بیشتر است.')

    def get_print_url(self):
        return  f'/ticket-qr/{self.tracking_code}/'

    def get_free_transaction_url(self):
        ticket_price = self.get_ticket_price()
        total_transactions = self.get_total_transactions()
        if total_transactions < ticket_price  :
            price = ticket_price-total_transactions
            return  f'/free_transaction/?ticket_id={self.id}&product_id={self.product.id}&qty={self.qty}&price={price}'
        else :
            return  f'/free_transaction/?ticket_id={self.id}'


    def get_ticket_status(self):
        ticket_price = self.get_ticket_price()
        total_transactions = self.get_total_transactions()
        price_difference = ticket_price-total_transactions
        if price_difference < 0  :
            status = f'مبلغ تراکنش ها {abs(price_difference)} ریال بیشتر از قیمت بلیت است.'
        elif price_difference > 0  :
            status = f'مبلغ تراکنش ها {price_difference} ریال کمتر از قیمت بلیت است.'
        else:
            status = 'مبلغ تراکنش برابر با مبلغ بلیت'
        return status
    
    def save(self, *args, **kwargs):
        self.product.order_metric += 1
        self.product.save()
        super(Ticket, self).save(*args, **kwargs)
