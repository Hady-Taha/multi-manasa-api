from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from core.utils import  send_whatsapp_massage
from student.models import *
from course.models import *
from invoice.models import *
from .models import Notification
from .tasks import notifications_custom_send
from core.utils import send_whatsapp_massage


@receiver(pre_save, sender=Invoice)
def pay_course(sender, instance, *args, **kwargs):
    if instance.pay_status == InvoicePayStatus.PAID:
        text = f"تم الاشتراك في {instance.item_name} بنجاح 🎉"
        
        # whatsapp massage
        send_whatsapp_massage(
            instance.student.user.username,
            text
        )
        
        notifications_custom_send.delay([instance.student.id],text)
        


#@receiver(pre_save, sender=Video)
#def new_video(sender, instance, *args, **kwargs):
##    if not instance.pending:
#       subscriptions_student_ids = Student.objects.filter(coursesubscription__course=instance.unit.course,coursesubscription__active=True).values_list("id",flat=True)
#        text=f"تمت إضافة درس جديد '{instance.name}' إلى الكورس '{instance.unit.course.name}'."
#        notifications_custom_send.delay(list(subscriptions_student_ids),text)
        

