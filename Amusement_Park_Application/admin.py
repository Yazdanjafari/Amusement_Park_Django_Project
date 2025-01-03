from django.contrib import admin
from .models import Product, Sale, TaxRate, Transaction, ReturnedSale, Ticket, TicketProduct, Category, Customer, Offer, SMS, Notification
from django.db.models import Sum, Count
from import_export.admin import ExportMixin
from import_export import resources
from import_export.fields import Field
from django.contrib.admin.widgets import FilteredSelectMultiple
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from import_export import resources, fields
from django.utils.translation import gettext_lazy as _

admin.site.site_header = 'پنل مدیریت وب اپلیکیشن شهربازی'


class CategoryAdmin(TreeAdmin):
    custom_widget = {'products': FilteredSelectMultiple("محصولات", is_stacked=False)}
    form = movenodeform_factory(Category, widgets=custom_widget)
    list_display = ('title', 'is_active', 'get_products')


class ProductAdminClass(admin.ModelAdmin):
    list_display = ('title', 'price', 'tourist_price', 'is_active', 'update')
    list_filter = ('title', 'price', 'created')
    search_fields = ('title',)


class TransactionResource(resources.ModelResource):
    j_create_at = Field(attribute='j_create_at', column_name='j_create_at')
    ticket__product__title = Field(attribute='ticket__product__title', column_name='ticket__product__title')

    class Meta:
        model = Transaction
        fields = ('id', 'type', 'is_success', 'ticket__product__title', 'price', 'trans_id', 'date', 'desc',
                  'create_at', 'user__last_name', 'user__username', 'j_create_at', 'has_tax', 'discount')


class TransactionAdminClass(admin.ModelAdmin):
    list_display = ('id', 'is_success', 'type', 'price', 'discount', 'trans_id', 'date', 'desc', 'ticket', 'j_create_at', 'user')
    list_filter = ('is_success', 'create_at', 'user', 'type')
    search_fields = ('id', 'desc')

    def has_add_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)
        extra_context = extra_context or {}

        extra_context.update({
            'total_price': queryset.aggregate(total_price=Sum('price'))['total_price'],
            'total_price_android_pos': queryset.filter(type=Transaction.TransactionType.card).aggregate(total_price_android_pos=Sum('price'))['total_price_android_pos'],
            'total_price_pc_pos': queryset.filter(type=Transaction.TransactionType.pc).aggregate(total_price_pc_pos=Sum('price'))['total_price_pc_pos'],
            'total_price_cash': queryset.filter(type=Transaction.TransactionType.cash).aggregate(total_price_cash=Sum('price'))['total_price_cash'],
        })

        return super().changelist_view(request, extra_context=extra_context)


class ProductSaleAdminClass(admin.ModelAdmin):
    list_display = ('id', 'type', 'price', 'discount', 'trans_id', 'date', 'desc', 'ticket', 'j_create_at', 'user')
    list_filter = ('create_at', 'user', 'type')
    search_fields = ('id', 'desc')


class ReturnedSaleAdmin(admin.ModelAdmin):
    # Fields to be displayed in the admin list view
    list_display = ('id', 'ticket', 'type', 'desc', 'user', 'j_create_at')
    
    # Add search capability to the admin
    search_fields = ('ticket__tracking_code', 'type', 'desc', 'user__username')
    
    # Filter options in the admin panel
    list_filter = ('type', 'user', 'create_at')

    # Ordering of the list view
    ordering = ('-create_at',)
    
    # Fields to display in the edit form
    fieldsets = (
        (None, {
            'fields': ('ticket', 'type', 'desc', 'user')
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
        fields = ('id', 'tracking_code', 'is_scanned', 'desc', 'is_tourist', 'user__last_name', 'user__username', 'j_create_at')

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





admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdminClass)
admin.site.register(TaxRate)
admin.site.register(Transaction, TransactionAdminClass)
admin.site.register(Sale, ProductSaleAdminClass)
admin.site.register(ReturnedSale, ReturnedSaleAdmin)
admin.site.register(Ticket, TicketAdminClass)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Offer, OfferAdmin)
admin.site.register(SMS, SMSAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(TicketProduct, TicketProductAdmin)