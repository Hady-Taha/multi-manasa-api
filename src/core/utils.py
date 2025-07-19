import json
import requests
from django.conf import settings
from django.utils import timezone
import requests

def send_whatsapp_massage(phone_number, massage):

    if settings.USE_WHATSAPP:
        url = "https://whats.easytech-sotfware.com/api/v1/send-text"

        params = {
                "token": settings.WHATSAPP_TOKEN,
                "instance_id": settings.WHATSAPP_ID,
                "msg": massage,
                "jid": f"2{phone_number}@s.whatsapp.net"
            }

        req = requests.get(url, params=params)
        print(req.text)
        return req.json()