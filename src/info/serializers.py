from rest_framework import serializers
from .models import *

class TeacherInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherInfo
        fields = '__all__' 

#^======================Centers======================^#

class CenterSerializer(serializers.ModelSerializer):
    timing_count = serializers.IntegerField(source='timing_set.count', read_only=True)
    timing_active_count = serializers.SerializerMethodField()
    class Meta:
        model = Center
        fields = [
            'id',
            'name',
            'address',
            'phone_number',
            'government',
            'timing_count',
            'timing_active_count',
            'created',
        ]

    def get_timing_active_count(self, obj):
        return obj.timing_set.filter(is_available=True).count()
    

class TimingSerializer(serializers.ModelSerializer):
    year_name = serializers.CharField(source='year.name', read_only=True)
    center_name = serializers.CharField(source='center.name', read_only=True)
    class Meta:
        model = TimingCenter
        fields = [
            'id',
            'day',
            'center_name',
            'year_name',
            'is_available',
            'year',
            'center',
            'created',
        ]

#^======================Books & Distributor ======================^#

class DistributorSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Distributor
        fields = [
            'id',
            'name',
            'phone_number',
            'government',
            'address',
            'created',
        ]
    

class DistributorBookSerializer(serializers.ModelSerializer):
    distributor_id = serializers.IntegerField(source='distributor.id', read_only=True)
    distributor_name = serializers.CharField(source='distributor.name', read_only=True)
    distributor_government = serializers.CharField(source='distributor.government', read_only=True)
    book_name = serializers.CharField(source='book.name', read_only=True)
    book_id = serializers.IntegerField(source='book.id', read_only=True)
    book_cover = serializers.ImageField(source='book.cover', read_only=True)
    book_year = serializers.CharField(source='book.year.name', read_only=True)

    class Meta:
        model = DistributorBook
        fields = [
            'id',
            'distributor_name',
            'distributor_government',
            'is_available',
            'book_name',
            'book_id',
            'book_cover',
            'book_year',
            ]


class BookSerializer(serializers.ModelSerializer):
    year_name = serializers.CharField(source='year.name', read_only=True)
    class Meta:
        model = Book
        fields = [
            'id',
            'name',
            'cover',
            'year_name',
            'year',
            'created',
        ]