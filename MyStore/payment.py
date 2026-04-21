import razorpay
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class PaymentGateway:
    """Base Payment Gateway Class"""
    
    def __init__(self):
        self.gateway_name = "Base"
    
    def create_order(self, amount, currency='INR', receipt=None):
        raise NotImplementedError
    
    def verify_payment(self, payment_id, order_id, signature):
        raise NotImplementedError


class RazorpayGateway(PaymentGateway):
    """Razorpay Payment Gateway"""
    
    def __init__(self):
        super().__init__()
        self.gateway_name = "Razorpay"
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    
    def create_order(self, amount, currency='INR', receipt=None):
        """
        Create Razorpay order
        Amount should be in paise (multiply by 100)
        """
        try:
            amount_in_paise = int(Decimal(amount) * 100)
            
            order_data = {
                'amount': amount_in_paise,
                'currency': currency,
                'receipt': receipt or f'order_{amount}',
                'payment_capture': 1  # Auto capture
            }
            
            order = self.client.order.create(data=order_data)
            logger.info(f"Razorpay order created: {order['id']}")
            return order
            
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {str(e)}")
            raise
    
    def verify_payment(self, payment_id, order_id, signature):
        """Verify Razorpay payment signature"""
        try:
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            self.client.utility.verify_payment_signature(params_dict)
            logger.info(f"Payment verified: {payment_id}")
            return True
            
        except razorpay.errors.SignatureVerificationError as e:
            logger.error(f"Payment verification failed: {str(e)}")
            return False
    
    def get_payment_details(self, payment_id):
        """Fetch payment details"""
        try:
            payment = self.client.payment.fetch(payment_id)
            return payment
        except Exception as e:
            logger.error(f"Failed to fetch payment: {str(e)}")
            return None
    
    def refund_payment(self, payment_id, amount=None):
        """
        Refund a payment
        If amount is None, full refund is processed
        """
        try:
            if amount:
                amount_in_paise = int(Decimal(amount) * 100)
                refund = self.client.payment.refund(payment_id, amount_in_paise)
            else:
                refund = self.client.payment.refund(payment_id)
            
            logger.info(f"Refund processed: {refund['id']}")
            return refund
            
        except Exception as e:
            logger.error(f"Refund failed: {str(e)}")
            raise


class StripeGateway(PaymentGateway):
    """Stripe Payment Gateway"""
    
    def __init__(self):
        super().__init__()
        self.gateway_name = "Stripe"
        # Implement Stripe integration here
        pass


class PayPalGateway(PaymentGateway):
    """PayPal Payment Gateway"""
    
    def __init__(self):
        super().__init__()
        self.gateway_name = "PayPal"
        # Implement PayPal integration here
        pass


def get_payment_gateway(gateway_type='razorpay'):
    """Factory function to get payment gateway instance"""
    gateways = {
        'razorpay': RazorpayGateway,
        'stripe': StripeGateway,
        'paypal': PayPalGateway,
    }
    
    gateway_class = gateways.get(gateway_type.lower())
    if not gateway_class:
        raise ValueError(f"Unsupported payment gateway: {gateway_type}")
    
    return gateway_class()
