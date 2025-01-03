from django.contrib import admin
from .models import Product, Sale, TaxRate, Transaction, ReturnedSale, ProductSaleReport, Ticket, Category, Costumer, Offer, SMS, Refund, RefundProduct, Notification
from django.db.models import Sum, Count
from import_export.admin import ExportMixin
from import_export import resources
from import_export.fields import Field
from django.contrib.admin.widgets import FilteredSelectMultiple
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory


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


class TransactionAdminClass(ExportMixin, admin.ModelAdmin):
    resource_classes = [TransactionResource]
    list_display = ('id', 'is_success', 'type', 'price', 'discount', 'trans_id', 'date', 'desc', 'ticket', 'j_create_at', 'user')
    list_filter = ('ticket__product', 'is_success', 'create_at', ("create_at"), 'user', 'type')
    search_fields = ('ticket__product__title', 'id', 'desc')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_export_queryset(request)
        extra_context = extra_context or {}

        extra_context.update({
            'total_price': queryset.aggregate(total_price=Sum('price'))['total_price'],
            'total_price_android_pos': queryset.filter(type=Transaction.TransactionType.card).aggregate(total_price_android_pos=Sum('price'))['total_price_android_pos'],
            'total_price_pc_pos': queryset.filter(type=Transaction.TransactionType.pc).aggregate(total_price_pc_pos=Sum('price'))['total_price_pc_pos'],
            'total_price_cash': queryset.filter(type=Transaction.TransactionType.cash).aggregate(total_price_cash=Sum('price'))['total_price_cash'],
        })
        
        return super().changelist_view(request, extra_context=extra_context)


class ProductSaleAdminClass(TransactionAdminClass):
    list_display = ('id', 'type', 'price', 'discount', 'trans_id', 'date', 'desc', 'ticket', 'j_create_at', 'user')
    list_filter = ('ticket__product', 'create_at', ("create_at"), 'user', 'type', 'ticket__product__categories')
    search_fields = ('ticket__product__title', 'id', 'desc')


class ReturnedSaleResource(resources.ModelResource):
    j_create_at = Field(attribute='j_create_at', column_name='j_create_at')

    class Meta:
        model = ReturnedSale
        fields = ('type', 'product__title', 'qty', 'price', 'desc', 'create_at', 'user__last_name', 'user__username', 'j_create_at')


class ReturnedSaleAdminClass(ExportMixin, admin.ModelAdmin):
    resource_classes = [ReturnedSaleResource]
    list_display = ('product', 'type', 'qty', 'price', 'create_at', 'desc', 'j_create_at', 'user')
    list_filter = ('product', 'create_at', 'user', 'type')
    search_fields = ('product__title',)
    autocomplete_fields = ['product']
    readonly_fields = ('user',)

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)


class ProductSaleReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'trans_id', 'date', 'desc', 'j_create_at', 'user')
    list_filter = ('create_at', ("create_at"))

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

        metrics = {
            'sum_ticket_qty': Sum('ticket__qty'),
            'total_transactions': Count('id'),
            'total_sales': Sum('price'),
        }

        response.context_data['summary'] = list(
            qs.values('ticket__product__title').annotate(**metrics).order_by('-total_sales')
        )
        response.context_data['summary_total'] = dict(qs.aggregate(**metrics))

        return response


class TicketResource(resources.ModelResource):
    j_create_at = Field(attribute='j_create_at', column_name='j_create_at')

    class Meta:
        model = Ticket
        fields = ('id', 'product__title', 'qty', 'is_scanned', 'desc', 'create_at', 'user__last_name', 'user__username', 'j_create_at')


class TicketAdminClass(ExportMixin, admin.ModelAdmin):
    resource_classes = [TicketResource]
    list_display = ('id', 'product', 'qty', 'is_scanned', 'create_at', 'user')
    list_filter = ('product', 'is_scanned', 'user', 'create_at')
    search_fields = ('id',)
    readonly_fields = ('transaction', 'user', 'is_scanned')

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)



# Costumer Admin
class CostumerAdmin(admin.ModelAdmin):
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



# RefundProduct Admin
class RefundProductInline(admin.TabularInline):
    model = RefundProduct
    extra = 1
    fields = ('product', 'quantity')

# Refund Admin
class RefundAdmin(admin.ModelAdmin):
    list_display = ('refund_id', 'ticket_tracking_code', 'refund_date', 'customer_name', 'refund_price', 'transaction_type')
    search_fields = ('customer_name', 'refund_id__id', 'ticket_tracking_code__tracking_code')
    list_filter = ('transaction_type', 'refund_date')
    inlines = [RefundProductInline]
    ordering = ('-refund_date',)



# RefundProduct Admin (this is for managing RefundProducts directly if needed)
class RefundProductAdmin(admin.ModelAdmin):
    list_display = ('refund', 'product', 'quantity')
    search_fields = ('refund__customer_name', 'product__title')
    list_filter = ('refund', 'product')
    


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
admin.site.register(ReturnedSale, ReturnedSaleAdminClass)
admin.site.register(ProductSaleReport, ProductSaleReportAdmin)
admin.site.register(Ticket, TicketAdminClass)
admin.site.register(Costumer, CostumerAdmin)
admin.site.register(Offer, OfferAdmin)
admin.site.register(SMS, SMSAdmin)
admin.site.register(Refund, RefundAdmin)
admin.site.register(RefundProduct, RefundProductAdmin)
admin.site.register(Notification, NotificationAdmin)