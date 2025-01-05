from django.contrib import admin
from .models import Product, TaxRate, Transaction, ReturnedTransaction, Ticket, TicketProduct, Category, Customer, Offer, SMS, Notification, RerecordingTransaction
from django.db.models import Sum
from import_export.admin import ExportMixin
from import_export import resources
from import_export.fields import Field
from django.contrib.admin.widgets import FilteredSelectMultiple
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from import_export import resources, fields
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver


admin.site.site_header = 'پنل مدیریت وب اپلیکیشن شهربازی'


class CategoryAdmin(TreeAdmin):
    custom_widget = {'products': FilteredSelectMultiple("محصولات", is_stacked=False)}
    form = movenodeform_factory(Category, widgets=custom_widget)
    list_display = ('title', 'is_active', 'get_products')


class ProductAdminClass(admin.ModelAdmin):
    list_display = ('title', 'price', 'is_active', 'is_taxable')
    list_filter = ('title', 'price', 'created')
    search_fields = ('title',)


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
    list_display = ('ticket', 'product', 'quantity')
    list_filter = ('ticket', 'product')




# Ticket Admin
class TicketResource(resources.ModelResource):
    j_create_at = fields.Field(attribute='j_create_at', column_name='j_create_at')

    class Meta:
        model = Ticket
        fields = ('id', 'tracking_code', 'is_scanned', 'desc', 'user__last_name', 'user__username', 'j_create_at')

    def dehydrate(self, ticket):
        ticket_products = TicketProduct.objects.filter(ticket=ticket)
        products = ', '.join([f"{tp.product.title} ({tp.quantity})" for tp in ticket_products])
        return products

    def dehydrate_j_create_at(self, ticket):
        return ticket.j_create_at()

class TicketAdminClass(ExportMixin, admin.ModelAdmin):
    resource_classes = [TicketResource]
    list_display = ('id', 'get_products', 'is_scanned', 'create_at', 'user')
    list_filter = ('is_scanned', 'user', 'create_at')
    search_fields = ('id',)
    readonly_fields = ('transaction', 'user', 'is_scanned')
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




# Customer Admin
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'date_of_birth', 'first_purchase', 'last_purchase')
    search_fields = ('first_name', 'last_name', 'phone')
    list_filter = ('date_of_birth', 'first_purchase', 'last_purchase')
    ordering = ('-last_purchase',)



# Offer Admin
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'persent', 'code', 'activate', 'set_up_time')
    search_fields = ('title', 'code')
    list_filter = ('activate', 'set_up_time')
    ordering = ('-set_up_time',)



# SMS Admin
class SMSAdmin(admin.ModelAdmin):
    list_display = ('title', 'target', 'activate', 'set_up_time')
    search_fields = ('title', 'target')
    list_filter = ('activate', 'set_up_time')
    ordering = ('-set_up_time',)


# Notification Admin
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'activate_time', 'activate', 'set_up_time')
    search_fields = ('title', 'activate_time')
    list_filter = ('activate', 'set_up_time')
    ordering = ('-set_up_time',)



# _____________________________________________ MAIN SELLING SYSTEM _____________________________________________ #

class TransactionAdminClass(admin.ModelAdmin):
    list_display = ('id', 'is_success', 'product_prices', 'tax', 'discount', 'price', 'type', 'user', 'ticket', 'j_create_at')
    list_filter = ('is_success', 'create_at', 'user', 'type')
    search_fields = ('id', 'desc')
    ordering = ('-create_at',)
    readonly_fields = ('create_at', 'tracking_code', 'product_prices', 'price', 'tax', 'discount', 'price')

    fieldsets = (
        (None, {
            'fields': ('user', 'ticket', 'type', 'is_success', 'has_tax', 'offer', 'manual_discount', 'desc')
        }),
        ('اتوماتیک', {
            'fields': ('tracking_code', 'product_prices', 'tax', 'discount', 'price', 'create_at')
        }),
    )

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
        total_card_sales = queryset.filter(type='card').aggregate(total_card=Sum('price'))['total_card'] or 0

        # Add all totals to extra_context
        extra_context = extra_context or {}
        extra_context.update({
            'total_product_prices': totals['total_product_prices'] or 0,
            'total_price': totals['total_price'] or 0,
            'total_tax': totals['total_tax'] or 0,
            'total_discount': totals['total_discount'] or 0,
            'total_pc_sales': total_pc_sales,
            'total_cash_sales': total_cash_sales,
            'total_card_sales': total_card_sales,
        })

        return super().changelist_view(request, extra_context=extra_context)



class RerecordingTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'rerecording_transaction', 'type', 'is_success', 'j_create_at')  # Display these fields in the list view
    list_filter = ('type', 'is_success', 'create_at')  # Add filter options in the sidebar
    search_fields = ('rerecording_transaction__id', 'desc')  # Enable search for transaction code and description
    ordering = ('-create_at',)  # Default ordering by creation date, most recent first
    readonly_fields = ('create_at',)  # Make the creation date field read-only

    fieldsets = (
        (None, {
            'fields': ('rerecording_transaction', 'type', 'is_success', 'desc', 'create_at')
        }),
    )



class ReturnedTransactionAdmin(admin.ModelAdmin):
    # Fields to be displayed in the admin list view
    list_display = ('id', 'transaction', 'type', 'desc', 'user', 'j_create_at')
    
    # Add search capability to the admin
    search_fields = ('transaction__tracking_code', 'type', 'desc', 'user__username')
    
    # Filter options in the admin panel
    list_filter = ('type', 'user', 'create_at')

    # Ordering of the list view
    ordering = ('-create_at',)
    
    # Fields to display in the edit form
    fieldsets = (
        (None, {
            'fields': ('transaction', 'type', 'desc', 'user')
        }),
        (_('Timestamps'), {
            'fields': ('create_at',)
        }),
    )

    # Making the 'create_at' field read-only
    readonly_fields = ('create_at',)

    # Display 'create_at' with Jalali date format
    def j_create_at(self, obj):
        return obj.j_create_at()
    j_create_at.short_description = _('Create Date')




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





