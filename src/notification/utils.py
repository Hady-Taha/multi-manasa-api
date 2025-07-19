import os
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from student.models import StudentMobileNotificationToken

cred_path = os.path.join(settings.BASE_DIR, 'firebase_key.json')

if not firebase_admin._apps:
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        raise FileNotFoundError(f"Firebase key not found at {cred_path}")


def send_push_notification(student, title, body, data=None):
    tokens = StudentMobileNotificationToken.objects.filter(student=student).values_list("token", flat=True)

    for token in tokens:
        if token:

            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                token=token,
                data=data or {}
            )
            response = messaging.send(message)


