from django.contrib import admin
from .models import Invoice, PromoCode

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'student', 'pay_status', 'pay_method',
        'amount', 'item_type', 'item_name', 'sequence',
        'pay_code', 'pay_at', 'expires_at', 'created'
    )
    list_filter = ('pay_status', 'pay_method', 'item_type', 'created')
    search_fields = ('sequence', 'pay_code', 'student__user__username', 'item_name','item_barcode')
    readonly_fields = (
        'sequence', 
        'created', 
        'updated', 
        'pay_at',
        'item_barcode',
        'item_name',
        'item_price',
        )

    ordering = ('-created',)

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'discount_percent', 'expiration_date',
        'usage_limit', 'used_count', 'is_active', 'created'
    )
    list_filter = ('is_active',)
    search_fields = ('code',)
    readonly_fields = ('used_count', 'created', 'updated')