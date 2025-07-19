from django_filters import rest_framework as filters
from django.utils import timezone
from invoice.models import Invoice
from .models import RequestLog
from view.models import ViewSession
import django_filters
import datetime

class InvoiceFilter(django_filters.FilterSet):
    created = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Invoice
        fields = ['student','item_type','item_barcode', 'pay_status', 'pay_method',  'created','student__year']



#^---------------------logs-----------------

class RequestLogFilter(filters.FilterSet):
    timestamp_after = filters.DateFilter(field_name='timestamp', lookup_expr='gte', method='filter_timestamp_after')
    timestamp_before = filters.DateFilter(field_name='timestamp', lookup_expr='lte', method='filter_timestamp_before')
    
    def filter_timestamp_after(self, queryset, name, value):
        # Convert date to datetime with time set to 00:00:00
        start_datetime = timezone.make_aware(datetime.datetime.combine(value, datetime.time.min))
        return queryset.filter(timestamp__gte=start_datetime)
    
    def filter_timestamp_before(self, queryset, name, value):
        # Convert date to datetime with time set to 23:59:59
        end_datetime = timezone.make_aware(datetime.datetime.combine(value, datetime.time.max))
        return queryset.filter(timestamp__lte=end_datetime)
    
    class Meta:
        model = RequestLog
        fields = {
            'user': ['exact'],
            'method': ['exact'],
            'status_code': ['exact'],
            'path': ['icontains'],
            'timestamp': ['exact'],  
        }



#^------------------

class ViewSessionFilter(django_filters.FilterSet):
    created_from = filters.DateFilter(field_name="created", lookup_expr="gte")
    created_to = filters.DateFilter(field_name="created", lookup_expr="lte")

    class Meta:
        model = ViewSession
        fields = [
            'session', 
            'view',
            'view__video',
            'view__student',
            'view__student__year',
            'created_from', 
            'created_to'
            ]



class ViewSessionFilterAnalysis(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="created", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="created", lookup_expr="lte")

    class Meta:
        model = ViewSession
        fields = ['start_date', 'end_date']