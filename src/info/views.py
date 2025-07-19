from rest_framework.views import APIView
from rest_framework import generics, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
# Create your views here.


class TeacherInfoListView(generics.ListAPIView):
    permission_classes = []
    queryset = TeacherInfo.objects.all()
    serializer_class = TeacherInfoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]


#^======================Centers======================^#

class CenterListView(generics.ListAPIView):
    permission_classes = []
    queryset = Center.objects.all()
    serializer_class = CenterSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]


class TimingCenterListView(generics.RetrieveAPIView):
    permission_classes = []
    queryset = TimingCenter.objects.all()
    serializer_class = TimingSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    lookup_url_kwarg = 'center_id'
    lookup_field = 'id'

#^======================Books & Distributor ======================^#

class BookListView(generics.ListAPIView):
    permission_classes = []
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name']


class DistributorListView(generics.ListAPIView):
    permission_classes = []
    queryset = Distributor.objects.all()
    serializer_class = DistributorSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name']


class DistributorBooksList(generics.ListAPIView):
    permission_classes = []
    queryset = DistributorBook.objects.all()
    serializer_class = DistributorBookSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['distributor__name']
    filterset_fields = ['distributor__id','book__id']