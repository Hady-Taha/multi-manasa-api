from rest_framework import serializers
from django.utils.dateparse import parse_date
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import datetime, time
from invoice.models import Invoice 

class InvoiceChartFilterSerializer(serializers.Serializer):
    pay_status = serializers.CharField(required=False)
    pay_method = serializers.CharField(required=False)
    item_type = serializers.CharField(required=False)
    item_barcode = serializers.CharField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    def _csv_to_list(self, value):
        if not value:
            return []
        return [v.strip() for v in value.split(",") if v.strip()]

    def get_queryset(self):
        data = self.validated_data

        queryset = Invoice.objects.all()

        if "pay_status" in data:
            queryset = queryset.filter(pay_status__in=self._csv_to_list(data["pay_status"]))
        if "pay_method" in data:
            queryset = queryset.filter(pay_method__in=self._csv_to_list(data["pay_method"]))
        if "item_type" in data:
            queryset = queryset.filter(item_type__in=self._csv_to_list(data["item_type"]))
        if "item_barcode" in data:
            queryset = queryset.filter(item_barcode=data["item_barcode"])
        if "start_date" in data:
            queryset = queryset.filter(pay_at__gte=datetime.combine(data["start_date"], time.min))
        if "end_date" in data:
            queryset = queryset.filter(pay_at__lte=datetime.combine(data["end_date"], time.max))

        return queryset

    def get_chart_data(self):
        queryset = self.get_queryset()

        monthly = (
            queryset.annotate(month=TruncMonth('pay_at'))
                    .values('month')
                    .annotate(total=Sum('amount'))
                    .order_by('month')
        )

        labels = [m["month"].strftime("%Y-%m") for m in monthly]
        data = [float(m["total"]) for m in monthly]

        return {
            "labels": labels,
            "data": data,
            "filters_used": self.validated_data
        }
