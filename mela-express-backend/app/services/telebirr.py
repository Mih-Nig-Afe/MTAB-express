"""Telebirr & CBE Birr Payment Service."""
import uuid
import hmac
import hashlib
import base64
import httpx
from datetime import datetime, timezone
from app.config import settings

class TelebirrService:
    def __init__(self):
        self.app_id = "TELEBIRR_APP_ID"
        self.app_key = "TELEBIRR_APP_KEY"
        self.short_code = "100123"
        self.api_url = "https://app.ethiomobilemoney.et:2121/ammapi/payment/service-openup/toTradeWebPay"

    def generate_payment_payload(self, parcel_id: str, amount: float, tracking_code: str) -> dict:
        """Generates dynamic Telebirr checkout data."""
        out_trade_no = f"TB-{tracking_code}-{uuid.uuid4().hex[:6]}"
        return {
            "out_trade_no": out_trade_no,
            "amount": str(amount),
            "currency": "ETB",
            "subject": f"Delivery Fee for {tracking_code}",
            "short_code": self.short_code,
            "notify_url": f"{settings.api_v1_str}/payments/telebirr/webhook",
            "return_url": f"https://mela-express.com/track/{tracking_code}?paid=true",
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
            "checkout_url": f"https://telebirr.et/pay?trade_no={out_trade_no}&amount={amount}"
        }

    def generate_cbe_qr_string(self, parcel_id: str, amount: float, tracking_code: str) -> str:
        """Generates CBE Birr dynamic QR code payload string."""
        return f"cbebirr://pay?till=890123&ref={tracking_code}&amt={amount}&name=MelaExpress"

telebirr_service = TelebirrService()
