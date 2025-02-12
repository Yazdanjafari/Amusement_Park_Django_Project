from django.contrib import admin
from .models import Product, TaxRate, Transaction, ReturnedTransaction, Ticket, TicketProduct, Category, Customer, Offer, SMS, Notification, RerecordingTransaction, ProductSaleReport, SellerSaleReport, CustomerPurchaseReport
from import_export.admin import ExportMixin
from import_export import resources
from import_export.fields import Field
from django.contrib.admin.widgets import FilteredSelectMultiple
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from import_export import resources, fields
from django.utils.translation import gettext_lazy as _
from django.db.models import F, Sum, Count, Q
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


admin.site.site_header = 'پنل مدیریت وب اپلیکیشن شهربازی'
admin.site.site_title = "پنل مدیریت"
admin.site.index_title = "پنل مدیریت"


class CategoryAdmin(TreeAdmin):
    custom_widget = {'products': FilteredSelectMultiple("محصولات", is_stacked=False)}
    form = movenodeform_factory(Category, widgets=custom_widget)
    list_display = ('title', 'is_active', 'get_products')


class ProductAdminClass(admin.ModelAdmin):
    list_display = ('title', 'formatted_price', 'is_active', 'is_taxable')
    list_filter = ('title', 'price', 'created')
    search_fields = ('title',)
    
    def formatted_price(self, obj):
        return '{:,}'.format(obj.price)  # Format the price with commas
    formatted_price.admin_order_field = 'price'  # Allow sorting by price
    formatted_price.short_description = 'قیمت'  # Set a custom label for the column    


class TransactionResource(resources.ModelResource):
    j_create_at = Field(attribute='j_create_at', column_name='j_create_at')
    ticket__product__title = Field(attribute='ticket__product__title', column_name='ticket__product__title')

    class Meta:
        model = Transaction
        fields = ('id', 'type', 'is_success', 'ticket__product__title', 'price', 'tracking_code', 'date', 'desc',
                  'create_at', 'user__last_name', 'user__username', 'j_create_at', 'has_tax', 'discount')




# TicketProduct Admin
class TicketProductInline(admin.TabularInline):
    model = TicketProduct
    extra = 1
    fields = ('product', 'quantity')


# RefundProduct Admin (this is for managing RefundProducts directly if needed)
class TicketProductAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'product', 'quantity', 'scanned')
    list_filter = ('ticket', 'product', 'scanned')
    
    def has_change_permission(self, request, obj = ...):
        return False
    
    def has_delete_permission(self, request, obj = ...):
        return False




# Ticket Admin
class TicketResource(resources.ModelResource):
    j_create_at = fields.Field(attribute='j_create_at', column_name='j_create_at')

    class Meta:
        model = Ticket
        fields = ('id', 'tracking_code', 'desc', 'user__last_name', 'user__username', 'j_create_at')

    def dehydrate(self, ticket):
        ticket_products = TicketProduct.objects.filter(ticket=ticket)
        products = ', '.join([f"{tp.product.title} ({tp.quantity})" for tp in ticket_products])
        return products

    def dehydrate_j_create_at(self, ticket):
        return ticket.j_create_at()
 
class TicketAdminClass(ExportMixin, admin.ModelAdmin):
    resource_classes = [TicketResource]
    list_display = ('id', 'get_products', 'create_at', 'user', 'customer')
    list_filter = ('user', 'create_at')
    search_fields = ('id',)
    readonly_fields = ('transaction', 'user')
    inlines = [TicketProductInline]

    def get_products(self, obj):
        return ', '.join([f"{tp.product.title} ({tp.quantity})" for tp in obj.ticket_products.all()])
    get_products.short_description = 'Products'

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)

        # Recalculate product_prices for related transactions
        total_price = obj.ticket_products.aggregate(
            total=Sum('product__price', field="product__price * quantity")
        )['total'] or 0

        for transaction in obj.transaction.all():
            transaction.product_prices = total_price
            transaction.save()

    def has_delete_permission(self, request, obj = ...):
        return False




# Customer Admin
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'phone', 'date_of_birth', 'j_first_purchase', 'j_last_purchase')
    search_fields = ('first_name', 'last_name', 'phone')
    list_filter = ('date_of_birth', 'first_purchase', 'last_purchase')
    ordering = ('-last_purchase',)
    
    def j_first_purchase(self, obj):
        return obj.j_first_purchase
    j_first_purchase.short_description = 'تاریخ اولین خرید'

    def j_last_purchase(self, obj):
        return obj.j_last_purchase
    j_last_purchase.short_description = 'تاریخ آخرین خرید'
    
# Offer Admin
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'persent', 'activate', 'j_create_at')
    search_fields = ('code', 'persent')
    list_filter = ('activate', 'create_at')
    ordering = ('-create_at',)

    def j_create_at(self, obj):
        return obj.j_create_at()
    j_create_at.short_description = 'تاریخ ایجاد'



# SMS Admin
class SMSAdmin(admin.ModelAdmin):
    list_display = ('title', 'target', 'activate', 'j_create_at')
    search_fields = ('title', 'target')
    list_filter = ('activate', 'j_create_at')
    ordering = ('-j_create_at',)

    def j_create_at(self, obj):
        return obj.j_create_at()
    j_create_at.short_description = 'تاریخ ایجاد'



# Notification Admin
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'activate', 'description', 'j_create_at')  # Fixed missing comma
    search_fields = ('title',)
    list_filter = ('activate', 'create_at')
    ordering = ('-create_at',)
    
    def j_create_at(self, obj):
        # Ensure the `j_create_at` method exists in the Notification model
        return obj.j_create_at()
    j_create_at.short_description = _('تاریخ ایجاد')  # Set the column header name



# _____________________________________________ MAIN SELLING SYSTEM _____________________________________________ #

class TransactionAdminClass(admin.ModelAdmin):
    list_display = ('id', 'is_success', 'formatted_product_prices', 'formatted_tax', 'formatted_discount', 'formatted_price', 'type', 'user', 'ticket', 'j_create_at')
    list_filter = ('is_success', 'create_at', 'user', 'type')
    search_fields = ('id', 'desc')
    ordering = ('-create_at',)
    readonly_fields = ('create_at', 'tracking_code', 'product_prices', 'price', 'tax', 'discount', 'price')

    fieldsets = (
        (None, {
            'fields': ('user', 'ticket', 'type', 'is_success', 'has_tax', 'offer', 'manual_discount', 'desc')
        }),
        ('فروش ترکیبی', {
            'fields': ('mix_pc', 'mix_cash')
        }),
        ('اتوماتیک', {
            'fields': ('tracking_code', 'product_prices', 'tax', 'discount', 'price', 'create_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        try:
            obj.save()
        except ValidationError as e:
            form.add_error(None, e.message)
            return
        super().save_model(request, obj, form, change)

    def formatted_product_prices(self, obj):
        if obj.product_prices is not None:
            return '{:,}'.format(obj.product_prices)  # Format the product_prices with commas
        return ''  # Return an empty string if product_prices is None
    formatted_product_prices.admin_order_field = 'product_prices'  # Allow sorting by product_prices
    formatted_product_prices.short_description = 'مجموع مبلغ محصولات'  # Set a custom label for the column

    def formatted_tax(self, obj):
        if obj.tax is not None:
            return '{:,}'.format(obj.tax)  # Format the tax with commas
        return ''  # Return an empty string if tax is None
    formatted_tax.admin_order_field = 'tax'  # Allow sorting by tax
    formatted_tax.short_description = 'مبلغ مالیات'  # Set a custom label for the column

    def formatted_discount(self, obj):
        if obj.discount is not None:
            return '{:,}'.format(obj.discount)  # Format the discount with commas
        return ''  # Return an empty string if discount is None
    formatted_discount.admin_order_field = 'discount'  # Allow sorting by discount
    formatted_discount.short_description = 'مبلغ تخفیف'  # Set a custom label for the column

    def formatted_price(self, obj):
        if obj.price is not None:
            return '{:,}'.format(obj.price)  # Format the price with commas
        return ''  # Return an empty string if price is None
    formatted_price.admin_order_field = 'price'  # Allow sorting by price
    formatted_price.short_description = 'قیمت نهایی'  # Set a custom label for the column


    def changelist_view(self, request, extra_context=None):
        # Filter the queryset for `is_success=True`
        queryset = self.get_queryset(request).filter(is_success=True)

        # Calculate totals for product prices, price, tax, discount
        totals = queryset.aggregate(
            total_product_prices=Sum('product_prices'),
            total_price=Sum('price'),
            total_tax=Sum('tax'),
            total_discount=Sum('discount')
        )

        # Calculate totals for sales from each payment method
        total_pc_sales = queryset.filter(type='pc').aggregate(total_pc=Sum('price'))['total_pc'] or 0
        total_cash_sales = queryset.filter(type='cash').aggregate(total_cash=Sum('price'))['total_cash'] or 0
        total_mix_sales = queryset.filter(type='mix').aggregate(total_mix=Sum('price'))['total_mix'] or 0

        # Calculate totals for mix_pc and mix_cash
        total_mix_pc = queryset.filter(type='mix').aggregate(total_mix_pc=Sum('mix_pc'))['total_mix_pc'] or 0
        total_mix_cash = queryset.filter(type='mix').aggregate(total_mix_cash=Sum('mix_cash'))['total_mix_cash'] or 0

        # Add all totals to extra_context
        extra_context = extra_context or {}
        extra_context.update({
            'total_product_prices': totals['total_product_prices'] or 0,
            'total_price': totals['total_price'] or 0,
            'total_tax': totals['total_tax'] or 0,
            'total_discount': totals['total_discount'] or 0,
            'total_pc_sales': total_pc_sales,
            'total_cash_sales': total_cash_sales,
            'total_mix_sales': total_mix_sales,
            'total_mix_pc': total_mix_pc,  
            'total_mix_cash': total_mix_cash,  #
        })

        return super().changelist_view(request, extra_context=extra_context)


    def has_delete_permission(self, request, obj = ...):
        return False


# _____________________________________________ ReturnedTransaction _____________________________________________ #
class RerecordingTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'rerecording_transaction', 'type', 'is_success', 'j_create_at')  # Display these fields in the list view
    list_filter = ('type', 'is_success', 'create_at')  # Add filter options in the sidebar
    search_fields = ('rerecording_transaction__id', 'desc')  # Enable search for transaction code and description
    ordering = ('-create_at',)  # Default ordering by creation date, most recent first
    readonly_fields = ('create_at',)  # Make the creation date field read-only

    fieldsets = (
        ("تراکنش", {
            'fields': ('rerecording_transaction', 'is_success', 'desc',)
        }),
        ("نوع پرداخت", {
            'fields': ('type', 'mix_pc', 'mix_cash',)
        }),
        ("تاریخ", {
            'fields': ('create_at',)
        }),
    )

    def has_delete_permission(self, request, obj = ...):
        return False

# _____________________________________________ ReturnedTransaction _____________________________________________ #
class ReturnedTransactionAdmin(admin.ModelAdmin):
    # Fields to be displayed in the admin list view
    list_display = ('id', 'transaction', 'type', 'desc', 'user', 'j_create_at')

    # Add search capability to the admin
    search_fields = ('transaction__tracking_code', 'type', 'desc')
    
    # Filter options in the admin panel
    list_filter = ('type', 'user', 'create_at')

    # Ordering of the list view
    ordering = ('-create_at',)
    
    # Fields to display in the edit form
    fieldsets = (
        (None, {
            'fields': ('transaction', 'type', 'user', 'desc')
        }),
        ("نوع عودت وجه", {
            'fields': ('source_card_holder_name', 'destination_card_holder_name', 'source_card_number', 'destination_card_number', 'source_sheba_number', 'destination_sheba_number')
        }),
        (_('Timestamps'), {
            'fields': ('create_at',)
        }),
    )

    # Making the 'create_at' field read-only
    readonly_fields = ('create_at',)

    # Display 'create_at' with Jalali date format
    def j_create_at(self, obj):
        # Assuming you have a method in your model that formats the date to Jalali
        return obj.j_create_at()  # Ensure this method exists in your model
    j_create_at.short_description = _('تاریخ ایجاد')

    def has_delete_permission(self, request, obj=None):
        return False


    # Add formatted display for refund prices
    def formatted_product_price(self, obj):
        return '{:,}'.format(obj.transaction.product_prices)  # Assuming the 'ReturnedTransaction' is linked to 'Transaction'
    formatted_product_price.short_description = _('Refund Product Price')

    def formatted_tax(self, obj):
        return '{:,}'.format(obj.transaction.tax)  # Link to the tax from the related transaction
    formatted_tax.short_description = _('Refund Tax')

    def formatted_discount(self, obj):
        return '{:,}'.format(obj.transaction.discount)  # Link to the discount from the related transaction
    formatted_discount.short_description = _('Refund Discount')

    def formatted_final_price(self, obj):
        return '{:,}'.format(obj.transaction.price)  # Link to the final price from the related transaction
    formatted_final_price.short_description = _('Final Refund Price')

    def changelist_view(self, request, extra_context=None):
        # Filter the queryset for valid refunds
        queryset = self.get_queryset(request)

        # Calculate totals for refunded product prices, taxes, discounts, and final price
        totals = queryset.aggregate(
            total_product_price=Sum('transaction__product_prices'),
            total_tax=Sum('transaction__tax'),
            total_discount=Sum('transaction__discount'),
            total_final_price=Sum('transaction__price'),
            total_cash_sales=Sum(
                'transaction__price',
                filter=Q(type=ReturnedTransaction.FoundType.cash)
            ),
            total_card_sales=Sum(
                'transaction__price',
                filter=Q(type=ReturnedTransaction.FoundType.send_money_by_card_number)
            ),
            total_pc_sales=Sum(
                'transaction__price',
                filter=Q(type=ReturnedTransaction.FoundType.send_money_by_sheba_number)
            )
        )

        # Add totals to extra_context
        extra_context = extra_context or {}
        extra_context.update({
            'total_product_price': totals['total_product_price'] or 0,
            'total_tax': totals['total_tax'] or 0,
            'total_discount': totals['total_discount'] or 0,
            'total_final_price': totals['total_final_price'] or 0,
            'total_cash_sales': totals['total_cash_sales'] or 0,
            'total_card_sales': totals['total_card_sales'] or 0,
            'total_pc_sales': totals['total_pc_sales'] or 0,
        })

        return super().changelist_view(request, extra_context=extra_context)

    


class ProductSaleReportAdmin(admin.ModelAdmin):
    # Ensure the list_filter is properly set
    list_filter = ('create_at',)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        # Define metrics for sales, including unsuccessful transactions
        metrics = {
            'total_transactions': Count('id'),
            'total_sales': Sum(F('ticket__ticket_products__quantity') * F('ticket__ticket_products__product__price')),
            'total_tickets': Sum('ticket__ticket_products__quantity'),
        }

        # Annotating with aggregated data for both successful and unsuccessful transactions
        summary_data = (
            TicketProduct.objects
            .select_related('product', 'ticket')
            .values('product__title')
            .annotate(
                total_transactions=Count('ticket'),
                total_sales=Sum(F('quantity') * F('product__price')),
                total_tickets=Sum('quantity'),
            )
        )

        # Add the summary data to the response context
        response.context_data['summary'] = summary_data

        # Add the total summary metrics to the context (including ticket count)
        response.context_data['summary_total'] = dict(
            qs.aggregate(**metrics)
        )

        return response





class SellerSaleReportAdmin(admin.ModelAdmin):
    list_filter = ('create_at',)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        # Define metrics for sales by users
        metrics = {
            'total_sales': Count('id'),  # Use Count for total sales (count of transactions)
            'total_revenue': Sum(F('ticket__ticket_products__quantity') * F('ticket__ticket_products__product__price')),
            'total_products_sold': Sum('ticket__ticket_products__quantity'),
        }

        # Aggregated data for seller reports (Ensure is_success=True)
        seller_data = (
            Transaction.objects
            .filter(is_success=True)  # Make sure only successful transactions are considered
            .values('user__first_name', 'user__last_name', 'user__id')  # Access first name, last name, and user id
            .annotate(
                total_sales=Count('id'),  # Count the number of transactions (sales)
                total_revenue=Sum(F('ticket__ticket_products__quantity') * F('ticket__ticket_products__product__price')),
                total_products_sold=Sum('ticket__ticket_products__quantity'),
            )
        )

        # Add user data to the context (first name, last name)
        for row in seller_data:
            row['user'] = get_user_model().objects.get(id=row['user__id'])

        response.context_data['summary'] = seller_data

        # Recalculate summary_total dynamically based on the latest transaction data
        summary_total = (
            Transaction.objects
            .filter(is_success=True)  # Ensure we're only looking at successful transactions
            .aggregate(
                total_sales=Count('id'),  # Count the number of transactions (sales)
                total_revenue=Sum(F('ticket__ticket_products__quantity') * F('ticket__ticket_products__product__price')),
                total_products_sold=Sum('ticket__ticket_products__quantity'),
            )
        )

        # Ensure that summary_total is not left as an outdated result
        response.context_data['summary_total'] = summary_total

        return response





# Customer Purchase Report Admin
class CustomerPurchaseReportAdmin(admin.ModelAdmin):
    list_filter = ('create_at',)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        # Define metrics for purchases by customers
        metrics = {
            'total_purchases': Count('id'),
            'total_spent': Sum(F('ticket__ticket_products__quantity') * F('ticket__ticket_products__product__price')),
            'total_products_purchased': Sum('ticket__ticket_products__quantity'),
        }

        # Aggregated data for customer purchase reports
        customer_data = (
            Transaction.objects
            .filter(is_success=True)  # Only successful transactions are considered
            .values('ticket__customer__first_name', 'ticket__customer__last_name', 'ticket__customer__id')
            .annotate(
                total_purchases=Count('id'),
                total_spent=Sum(F('ticket__ticket_products__quantity') * F('ticket__ticket_products__product__price')),
                total_products_purchased=Sum('ticket__ticket_products__quantity'),
            )
        )

        # Add customer data to the context, handling missing users
        for row in customer_data:
            try:
                row['customer'] = get_user_model().objects.get(id=row['ticket__customer__id'])
            except get_user_model().DoesNotExist:
                row['customer'] = None  # Or set to a placeholder value, e.g., "Unknown Customer"

        response.context_data['summary'] = customer_data

        # Recalculate summary_total dynamically based on the latest transaction data
        summary_total = (
            Transaction.objects
            .filter(is_success=True)
            .aggregate(
                total_purchases=Count('id'),
                total_spent=Sum(F('ticket__ticket_products__quantity') * F('ticket__ticket_products__product__price')),
                total_products_purchased=Sum('ticket__ticket_products__quantity'),
            )
        )

        response.context_data['summary_total'] = summary_total

        return response





# _____________________________________________ Registery _____________________________________________ #
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdminClass)
admin.site.register(TaxRate)
admin.site.register(Transaction, TransactionAdminClass)
admin.site.register(ReturnedTransaction, ReturnedTransactionAdmin)
admin.site.register(Ticket, TicketAdminClass)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Offer, OfferAdmin)
admin.site.register(SMS, SMSAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(TicketProduct, TicketProductAdmin)
admin.site.register(RerecordingTransaction, RerecordingTransactionAdmin)
admin.site.register(ProductSaleReport, ProductSaleReportAdmin)
admin.site.register(SellerSaleReport, SellerSaleReportAdmin)
admin.site.register(CustomerPurchaseReport, CustomerPurchaseReportAdmin)


