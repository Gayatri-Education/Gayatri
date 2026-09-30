"""Gayatri AI Platform — Mock Payment Gateway Adapter (Phase 32).

Deterministic in-memory payment provider for testing, offline execution,
and local development without external API keys.
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from central_platform.payments.base import (
    PaymentOrderResponse,
    PaymentProvider,
    PaymentRefundResponse,
    PaymentStatusResponse,
)


class MockPaymentAdapter(PaymentProvider):
    """Deterministic Mock Payment Adapter for development and testing."""

    def __init__(self, mock_secret: str = "mock_secret_key_12345"):
        self.mock_secret = mock_secret
        self._orders: Dict[str, Dict[str, Any]] = {}
        self._payments: Dict[str, Dict[str, Any]] = {}

    @property
    def provider_name(self) -> str:
        return "mock"

    def create_order(
        self,
        amount: float,
        currency: str = "INR",
        receipt_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentOrderResponse:
        order_id = f"order_mock_{uuid.uuid4().hex[:10]}"
        raw = {
            "id": order_id,
            "amount": amount,
            "currency": currency,
            "receipt": receipt_id,
            "status": "created",
            "metadata": metadata or {},
        }
        self._orders[order_id] = raw

        return PaymentOrderResponse(
            order_id=order_id,
            amount=amount,
            currency=currency,
            receipt_id=receipt_id,
            provider=self.provider_name,
            checkout_url=f"https://pay.gayatri.ai/mock/{order_id}",
            raw_payload=raw,
        )

    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        expected = hmac.new(
            self.mock_secret.encode("utf-8"),
            f"{order_id}|{payment_id}".encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def generate_mock_signature(self, order_id: str, payment_id: str) -> str:
        """Helper to generate valid signature for testing."""
        return hmac.new(
            self.mock_secret.encode("utf-8"),
            f"{order_id}|{payment_id}".encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
        secret: str,
    ) -> bool:
        expected = hmac.new(
            secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header)

    def fetch_payment_status(self, payment_id: str) -> PaymentStatusResponse:
        payment_data = self._payments.get(payment_id)
        if not payment_data:
            return PaymentStatusResponse(
                payment_id=payment_id,
                order_id="order_mock_000",
                status="captured",
                amount=1000.0,
                currency="INR",
                payment_method="upi",
                transaction_ref=f"TXN_{payment_id[:6]}",
                provider=self.provider_name,
            )
        return PaymentStatusResponse(
            payment_id=payment_id,
            order_id=payment_data.get("order_id", ""),
            status=payment_data.get("status", "captured"),
            amount=payment_data.get("amount", 0.0),
            currency=payment_data.get("currency", "INR"),
            payment_method=payment_data.get("payment_method", "upi"),
            transaction_ref=payment_data.get("transaction_ref", f"TXN_{payment_id[:6]}"),
            provider=self.provider_name,
        )

    def process_refund(
        self,
        payment_id: str,
        amount: float,
        reason: str = "",
    ) -> PaymentRefundResponse:
        refund_id = f"rfd_mock_{uuid.uuid4().hex[:10]}"
        return PaymentRefundResponse(
            refund_id=refund_id,
            payment_id=payment_id,
            amount=amount,
            currency="INR",
            status="processed",
            provider=self.provider_name,
        )
