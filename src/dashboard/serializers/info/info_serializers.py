from rest_framework import serializers
from info.models import *

class TeacherInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherInfo
        fields = '__all__' 


# Center
class CenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Center
        fields = '__all__'


class TimingCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimingCenter
        fields = '__all__'


# Books
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

# Distributor
class DistributorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Distributor
        fields = '__all__'


# Distributor Book
class DistributorBookSerializer(serializers.ModelSerializer):
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
