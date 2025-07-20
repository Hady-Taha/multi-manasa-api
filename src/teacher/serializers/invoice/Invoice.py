from rest_framework import serializers
from invoice.models import Invoice,PromoCode

class ListInvoiceSerializer(serializers.ModelSerializer):
    student__name = serializers.CharField(source="student.name")
    student__username = serializers.CharField(source="student.user.username")
    promo_code__code = serializers.CharField(source='promo_code.code', default=None)
    promo_code__discount_percent = serializers.CharField(source='promo_code.discount_percent', default='0')
    sequence_invoice = serializers.CharField(source="sequence")
    student_id = serializers.IntegerField(source="student.id")
    class Meta:
        model = Invoice
        fields = [
            'id',
            'student_id',
            'student__name',
            'student__username',
            'pay_status',
            'pay_method',
            'pay_code',
            'amount',
            'sequence_invoice',
            'item_type',
            'item_price',
            'item_name',
            'item_barcode',
            'expires_at',
            'promo_code__code',
            'promo_code__discount_percent',
            'created',
        ]
