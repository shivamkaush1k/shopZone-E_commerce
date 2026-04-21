from twilio.rest import Client
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_sms(phone_number, message):
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
        logger.warning("Twilio credentials not configured")
        return False
    
    # Format Indian numbers: +91XXXXXXXXXX
    if not phone_number.startswith('+91'):
        phone_number = '+91' + phone_number.lstrip('0') if phone_number.startswith('0') else '+91' + phone_number
    
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    try:
        msg = client.messages.create(body=message, from_=settings.TWILIO_PHONE_NUMBER, to=phone_number)
        logger.info(f"SMS sent: {msg.sid} to {phone_number}")
        return True
    except Exception as e:
        logger.error(f"SMS failed to {phone_number}: {e}")
        return False