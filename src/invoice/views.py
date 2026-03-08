import requests
import hashlib
import json
import uuid
from datetime import timedelta, datetime
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.exceptions import ValidationError
from student.models import Student
from course.models import Course,Video,CourseCode,VideoCode
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from .models import Invoice,InvoiceMethodPayType,InvoicePayStatus,InvoiceItemType,PromoCode
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal

# Create your views here.

#* < ==============================[ <- EasyPay -> ]============================== > ^#


class PayWithEasyPay(APIView):
    permission_classes = [IsAuthenticated]
    # add in models can_buy , price , free , barcode , name
    def post(self, request, *args, **kwargs):
        student = request.user.student
        item_type = request.data.get("item_type")
        item_barcode = request.data.get("item_barcode")
        promo_code_input = request.data.get("promo_code", "").strip()

        # Validate item_type
        if item_type not in InvoiceItemType.values:
            return Response({"detail": "Invalid item_type"}, status=400)

        model_map = {
            InvoiceItemType.COURSE: Course,
            InvoiceItemType.VIDEO: Video
        }

        model_class = model_map.get(item_type)
        try:
            item = model_class.objects.get(barcode=item_barcode)
        except model_class.DoesNotExist:
            return Response({"detail": "هذا العنصر غير موجود"}, status=404)

        if item.can_buy==False:
            return Response({"detail":"لا يمكن شراء هذا العنصر"},status=status.HTTP_400_BAD_REQUEST)


        # free item
        if item.price == 0 or item.free :
            invoice = Invoice.objects.create(
                teacher=item.teacher,
                student=student,
                pay_status=InvoicePayStatus.PAID,
                pay_method=InvoiceMethodPayType.FREE,
                amount=0,
                item_type=item_type,
                item_barcode=item.barcode,
                item_price=0,
                item_name=item.name,
                expires_at=timezone.now(),
                pay_at=timezone.now()
            )
            
            return Response({"detail": "Item is free and has been granted."}, status=200)

        
        # Start with original price
        final_price = Decimal(item.price)

        # APPLY COURSE DISCOUNT (percentage)
        if hasattr(item, 'discount') and item.discount > 0:
            course_discount_amount = (
                final_price * Decimal(item.discount) / Decimal('100')
            ).quantize(Decimal('0.01'))

            final_price -= course_discount_amount

        # Prevent negative price
        if final_price < 0:
            final_price = Decimal('0.00')

        applied_promo = None

        # APPLY PROMO CODE IF PRESENT
        if promo_code_input:
            try:
                promo = PromoCode.objects.get(code=promo_code_input)
            except PromoCode.DoesNotExist:
                return Response({"massage": "كود الخصم غير موجود"}, status=400)

            if not promo.is_valid():
                return Response({"massage": "انتهت صلاحية كود الخصم أو تجاوز الحد المسموح به"}, status=400)

            if promo.used_by_students.filter(id=student.id).exists():
                return Response({"massage": "لقد استخدمت هذا الكود من قبل"}, status=400)

            promo_discount_amount = (
                final_price * Decimal(promo.discount_percent) / Decimal('100')
            ).quantize(Decimal('0.01'))

            final_price -= promo_discount_amount

            if final_price < 0:
                final_price = Decimal('0.00')

            applied_promo = promo
            
            
        # PAID ITEM
        invoice=Invoice.objects.create(
            teacher=item.teacher,
            student=student,
            pay_method=InvoiceMethodPayType.EASY_PAY,
            promo_code=applied_promo,
            expires_at=timezone.now() + timedelta(days=2),
            amount=final_price,
            item_type=item_type,
            item_barcode=item.barcode,
            item_price=item.price,
            item_name=item.name,
        )
        
        if applied_promo:
            applied_promo.used_count += 1
            applied_promo.used_by_students.add(student)
            applied_promo.save()



        res_data=self.easy_pay_api(invoice)

        return Response(res_data,status=status.HTTP_200_OK)
    
    def easy_pay_api(self, invoice):
        student = invoice.student
        string_to_hash = f"{settings.EASY_PAY_CODE}{settings.EASY_PAY_SEC_KEY}{invoice.amount}{student.id}{student.user.username}"
        signature = hashlib.sha256(string_to_hash.encode('utf-8')).hexdigest()

        payment_data = {
            "vendor_code": f'{settings.EASY_PAY_CODE}',
            "amount": f'{invoice.amount}',
            "payment_expiry": int((datetime.now() + timedelta(days=4)).timestamp() * 1000),
            "signature": f'{signature}',
            "payment_method": "fawry",
            "customer": {
                "name": f'{student.name}',
                "phone": f'{student.user.username}',
                "profile_id": f'{student.id}'
            },
            "items": [
                {
                    "item_id": f'{invoice.item_barcode}',
                    "price": f'{invoice.amount}',
                    "Quantity": 1,
                    "description": f'{invoice.item_name}'
                }
            ]
        }

        response = requests.post(settings.EASY_PAY_URL, json=payment_data)

        try:
            data = response.json()
        except ValueError:
            print("Response is not JSON:", response.text)
            return {"error": "Invalid response from EasyPay"}  # Return dict instead of Response

        invoice.easy_pay_sequence = data['invoice_sequence']
        invoice.save()

        return data
    


class EasyPayCallBack(APIView):
    def post(self, request,api_key, *args, **kwargs):
        if api_key != settings.API_KEY_MANASA:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        easy_pay_sequence = request.data.get("easy_pay_sequence")
        status_paid = request.data.get("status")
        received_signature = request.data.get("signature")
        customer_phone = request.data.get("customer_phone")
        amount = request.data.get("amount")

        try:
            invoice = Invoice.objects.get(easy_pay_sequence=easy_pay_sequence)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)

        # Reconstruct the string and compute the expected signature
        string_to_hash = f"{amount}{customer_phone}{settings.EASY_PAY_SEC_KEY}"
        expected_signature = hashlib.sha256(string_to_hash.encode('utf-8')).hexdigest()

        # Compare signatures
        if received_signature != expected_signature:
            return Response({"error": "Invalid signature."}, status=status.HTTP_403_FORBIDDEN)

        if status_paid == 'PAID':
            invoice.pay_status = InvoicePayStatus.PAID
            invoice.pay_at = timezone.now()
            invoice.price = amount
            invoice.save()

        return Response({"message": "Callback processed successfully."}, status=status.HTTP_200_OK)
    


class GetPromoCodePercentView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, promo_code, *args, **kwargs):
        student = request.user.student
        code = promo_code.strip()

        try:
            promo = PromoCode.objects.get(code=code)
        except PromoCode.DoesNotExist:
            return Response({"massage": 'الكود غير موجود'},status=404)

        if not promo.is_active:
            return Response({"massage": 'انتهت صلاحية الكود'},status=400)

        if promo.expiration_date and timezone.now() > promo.expiration_date:
            return Response({"massage": 'انتهت صلاحية الكود'},status=400)

        if promo.usage_limit and promo.used_count >= promo.usage_limit:
            return Response({"massage": 'انتهت صلاحية الكود'},status=400)

        if promo.used_by_students.filter(id=student.id).exists():
            return Response({"massage": 'لقد استخدمة الكود من قبل'},status=400)

        return Response({"discount_percent": promo.discount_percent})



#* < ==============================[ <- CODE -> ]============================== > ^#

class PayWithCode(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        code_type = request.data.get("code_type")
        code = request.data.get("code")
        barcode = request.data.get("barcode")
        student = request.user.student

        if code_type == 'video':
            return self.handle_video_code(student, code, barcode)

        elif code_type == 'course':
            return self.handle_course_code(student, code, barcode)

        return Response(
            {"error": "Invalid code type."},
            status=status.HTTP_400_BAD_REQUEST
        )

    def handle_video_code(self, student, code, barcode):
        get_video_code = get_object_or_404(VideoCode, code=code)

        if not get_video_code.available:
            return Response(
                {"error": "The requested code is no longer available."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if get_video_code.video:
            self.create_invoice(
                student,
                get_video_code.video,
                InvoiceItemType.VIDEO,
                amount=get_video_code.price,
                code=get_video_code.code
            )
            get_video_code.available = False
            get_video_code.student = student
            get_video_code.save()
        else:
            get_video = get_object_or_404(Video, barcode=barcode)
            #*check if video is in belong the video
            
            self.create_invoice(
                student,
                get_video,
                InvoiceItemType.VIDEO,
                amount=get_video.price,
                code=get_video_code.code
            )
            get_video_code.available = False
            get_video_code.student = student
            get_video_code.video = get_video
            get_video_code.save()

        return Response(status=status.HTTP_200_OK)

    def handle_course_code(self, student, code, barcode):
        get_course_code = get_object_or_404(CourseCode, code=code)

        if not get_course_code.available:
            return Response(
                {"error": "The requested course code is no longer available."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if get_course_code.course:
            self.create_invoice(
                student,
                get_course_code.course,
                InvoiceItemType.COURSE,
                amount=get_course_code.price,
                code=get_course_code.code
            )
            get_course_code.available = False
            get_course_code.student = student
            get_course_code.save()
        else:
            course = get_object_or_404(Course, barcode=barcode)
            self.create_invoice(
                student,
                course,
                InvoiceItemType.COURSE,
                amount=course.price,
                code=course.code
            )
            get_course_code.available = False
            get_course_code.student = student
            get_course_code.course = course
            get_course_code.save()

        return Response(status=status.HTTP_200_OK)

    def create_invoice(self, student, item, item_type, amount, code):
        Invoice.objects.create(
            student=student,
            pay_method=InvoiceMethodPayType.CODE,
            pay_status=InvoicePayStatus.PAID,
            pay_code=code,
            expires_at=timezone.now() + timedelta(days=2),
            pay_at=timezone.now(),
            amount=amount,
            item_type=item_type,
            item_barcode=item.barcode,
            item_price=amount,
            item_name=item.name,
        )

